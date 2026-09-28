"""Admin-only endpoints: register users/bins, see customers and dashboard numbers.
The dependency on the router itself locks EVERY endpoint here to role 'admin'."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.core.security import hash_password
from app.models.complaint import Complaint
from app.models.customer import Customer, PaymentStatus
from app.models.fleet import Driver, Truck
from app.models.payment import Payment
from app.models.route import CollectionStop, Route
from app.models.user import Role, User
from app.models.waste_bin import WasteBin
from app.routing.planner import complete_stop, route_details, stop_dict
from app.core.config import settings
from app.schemas import (
    AdminCreate, AdminOut, BinCreate, BinOut, BinUpdate, CustomerCreate, CustomerOut,
    CustomerUpdate, DriverCreate, DriverOut,
)
from app.services.billing import today_tz
from app.services.customers import create_customer

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_roles(*Role.ADMINS))])
super_admin_only = Depends(require_roles(Role.SUPER_ADMIN))


# ---------- registering things ----------
@router.post("/customers", response_model=CustomerOut, status_code=201)
def register_customer(data: CustomerCreate, db: Session = Depends(get_db)):
    return create_customer(db, data)


@router.post("/drivers", status_code=201)
def register_driver(data: DriverCreate, db: Session = Depends(get_db)):
    """Creates the driver's login AND their truck in one step."""
    user = User(
        full_name=data.full_name,
        phone=data.phone,
        password_hash=hash_password(data.password),
        role=Role.DRIVER,
    )
    db.add(user)
    try:
        db.flush()
        driver = Driver(user_id=user.id)
        db.add(driver)
        db.flush()
        truck = Truck(plate_number=data.plate_number, driver_id=driver.id, fuel_km_per_liter=data.fuel_km_per_liter)
        db.add(truck)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Phone number or plate number is already registered")
    return {"driver_id": driver.id, "truck_id": truck.id, "plate_number": truck.plate_number}


@router.delete("/drivers/{driver_id}")
def remove_driver(driver_id: int, db: Session = Depends(get_db)):
    """Removes a driver: their login is disabled and their truck is taken out of routing.
    A route already generated today is left alone; regenerate routes after removing a driver."""
    driver = db.get(Driver, driver_id)
    if driver is None:
        raise HTTPException(404, "Driver not found")
    db.get(User, driver.user_id).is_active = False
    for truck in db.scalars(select(Truck).where(Truck.driver_id == driver_id)):
        truck.is_active = False
    db.commit()
    return {"ok": True}


@router.post("/bins", response_model=BinOut, status_code=201)
def register_bin(data: BinCreate, db: Session = Depends(get_db)):
    waste_bin = WasteBin(code=data.code, ward=data.ward, latitude=data.latitude, longitude=data.longitude)
    db.add(waste_bin)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "A bin with this code already exists")
    db.refresh(waste_bin)
    return waste_bin


# ---------- admins (super admin only: adding/removing admin accounts) ----------
@router.post("/admins", response_model=AdminOut, status_code=201, dependencies=[super_admin_only])
def register_admin(data: AdminCreate, db: Session = Depends(get_db)):
    """Creates a new (regular) admin login. Only a super admin can do this - a regular
    admin can do everything else here except add or remove other admins."""
    user = User(full_name=data.full_name, phone=data.phone, password_hash=hash_password(data.password), role=Role.ADMIN)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Phone number is already registered")
    db.refresh(user)
    return user


@router.get("/admins", response_model=List[AdminOut], dependencies=[super_admin_only])
def list_admins(db: Session = Depends(get_db)):
    return db.scalars(select(User).where(User.role.in_([Role.ADMIN, Role.SUPER_ADMIN])).order_by(User.id)).all()


@router.delete("/admins/{admin_id}", response_model=AdminOut, dependencies=[super_admin_only])
def remove_admin(admin_id: int, me: User = Depends(require_roles(Role.SUPER_ADMIN)), db: Session = Depends(get_db)):
    """Disables an admin's login. A super admin cannot remove themself or another super admin
    this way (to avoid ever locking every super admin out)."""
    target = db.get(User, admin_id)
    if target is None or target.role not in (Role.ADMIN, Role.SUPER_ADMIN):
        raise HTTPException(404, "Admin not found")
    if target.id == me.id:
        raise HTTPException(400, "You cannot remove your own admin account")
    if target.role == Role.SUPER_ADMIN:
        raise HTTPException(400, "A super admin account cannot be removed here")
    target.is_active = False
    db.commit()
    db.refresh(target)
    return target


@router.post("/admins/{admin_id}/reactivate", response_model=AdminOut, dependencies=[super_admin_only])
def reactivate_admin(admin_id: int, db: Session = Depends(get_db)):
    target = db.get(User, admin_id)
    if target is None or target.role not in (Role.ADMIN, Role.SUPER_ADMIN):
        raise HTTPException(404, "Admin not found")
    target.is_active = True
    db.commit()
    db.refresh(target)
    return target


# ---------- drivers/trucks (view) ----------
@router.get("/drivers", response_model=List[DriverOut])
def list_drivers(db: Session = Depends(get_db)):
    rows = db.execute(
        select(Driver, User, Truck).join(User, User.id == Driver.user_id).join(Truck, Truck.driver_id == Driver.id)
    ).all()
    return [
        DriverOut(
            driver_id=driver.id, user_id=user.id, full_name=user.full_name, phone=user.phone,
            plate_number=truck.plate_number, fuel_km_per_liter=truck.fuel_km_per_liter, is_active=user.is_active,
        )
        for driver, user, truck in rows
    ]


# ---------- viewing things ----------
@router.get("/customers", response_model=List[CustomerOut])
def list_customers(
    ward: Optional[str] = None,
    status: Optional[str] = None,  # registered | billed | paid
    include_inactive: bool = False,  # True = also show customers that were removed
    db: Session = Depends(get_db),
):
    q = select(Customer).join(User, User.id == Customer.user_id)
    if not include_inactive:
        q = q.where(User.is_active.is_(True))
    if ward:
        q = q.where(Customer.ward == ward)
    if status:
        q = q.where(Customer.payment_status == status)
    return db.scalars(q.order_by(Customer.id)).all()


@router.patch("/customers/{customer_id}", response_model=CustomerOut)
def update_customer(customer_id: int, data: CustomerUpdate, db: Session = Depends(get_db)):
    """Edits a customer's own details (name, phone, ward, address, location). Send only the
    fields that changed. Password and payment_status are not editable here."""
    customer = db.get(Customer, customer_id)
    if customer is None:
        raise HTTPException(404, "Customer not found")

    changes = data.model_dump(exclude_unset=True)
    if "full_name" in changes:
        customer.user.full_name = changes.pop("full_name")
    if "phone" in changes:
        new_phone = changes.pop("phone")
        customer.user.phone = new_phone  # phone is also the login name
        customer.phone = new_phone
    for field, value in changes.items():  # ward, address, latitude, longitude
        setattr(customer, field, value)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Namba hii ya simu tayari inatumiwa na mtumiaji mwingine")
    db.refresh(customer)
    return customer


@router.delete("/customers/{customer_id}", response_model=CustomerOut)
def remove_customer(customer_id: int, db: Session = Depends(get_db)):
    """Removes a customer from the system: they can no longer log in, they disappear from the
    live map and from future collection lists and billing runs. Their payment and complaint
    history is kept (not deleted), in case you need it later - that's why this deactivates
    the account instead of erasing the row."""
    customer = db.get(Customer, customer_id)
    if customer is None:
        raise HTTPException(404, "Customer not found")
    customer.user.is_active = False
    # Don't send a truck to someone who was just removed
    for stop in db.scalars(
        select(CollectionStop).where(CollectionStop.customer_id == customer_id, CollectionStop.status == "pending")
    ):
        db.delete(stop)
    db.commit()
    db.refresh(customer)
    return customer


@router.post("/customers/{customer_id}/reactivate", response_model=CustomerOut)
def reactivate_customer(customer_id: int, db: Session = Depends(get_db)):
    """Undo a removal: the customer can log in again and reappears on the map."""
    customer = db.get(Customer, customer_id)
    if customer is None:
        raise HTTPException(404, "Customer not found")
    customer.user.is_active = True
    db.commit()
    db.refresh(customer)
    return customer


@router.get("/bins", response_model=List[BinOut])
def list_bins(include_inactive: bool = False, db: Session = Depends(get_db)):
    q = select(WasteBin)
    if not include_inactive:
        q = q.where(WasteBin.is_active.is_(True))
    return db.scalars(q.order_by(WasteBin.id)).all()


@router.patch("/bins/{bin_id}", response_model=BinOut)
def update_bin(bin_id: int, data: BinUpdate, db: Session = Depends(get_db)):
    """Edit a bin's details - typically its location after it has been physically moved.
    Send only the fields that changed."""
    waste_bin = db.get(WasteBin, bin_id)
    if waste_bin is None:
        raise HTTPException(404, "Bin not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(waste_bin, field, value)
    db.commit()
    db.refresh(waste_bin)
    return waste_bin


@router.delete("/bins/{bin_id}", response_model=BinOut)
def remove_bin(bin_id: int, db: Session = Depends(get_db)):
    """Takes a bin out of service (e.g. it was removed/relocated). History (any past
    collection stops) is kept - this only hides it from new routes and the live map."""
    waste_bin = db.get(WasteBin, bin_id)
    if waste_bin is None:
        raise HTTPException(404, "Bin not found")
    waste_bin.is_active = False
    for stop in db.scalars(
        select(CollectionStop).where(CollectionStop.bin_id == bin_id, CollectionStop.status == "pending")
    ):
        db.delete(stop)
    db.commit()
    db.refresh(waste_bin)
    return waste_bin


@router.post("/bins/{bin_id}/reactivate", response_model=BinOut)
def reactivate_bin(bin_id: int, db: Session = Depends(get_db)):
    waste_bin = db.get(WasteBin, bin_id)
    if waste_bin is None:
        raise HTTPException(404, "Bin not found")
    waste_bin.is_active = True
    # Removing a bin deleted its waiting stop. If it is still full, put it back on the
    # collection list now instead of waiting for the sensor's next reading.
    if waste_bin.status == "full" and db.scalar(
        select(CollectionStop).where(CollectionStop.bin_id == bin_id, CollectionStop.status == "pending")
    ) is None:
        db.add(CollectionStop(stop_date=today_tz(), bin_id=bin_id))
    db.commit()
    db.refresh(waste_bin)
    return waste_bin


@router.post("/routes/stops/{stop_id}/complete")
def admin_complete_stop(stop_id: int, db: Session = Depends(get_db)):
    """Marks one stop as collected - the same action a driver does from their phone,
    available here too in case the driver can't (no phone, sensor found it already emptied,
    correcting a mistake, etc). A route finishes automatically once every one of its stops
    is marked complete this way or by the driver."""
    stop = db.get(CollectionStop, stop_id)
    route = db.get(Route, stop.route_id) if stop and stop.route_id else None
    if route is None:
        raise HTTPException(404, "Stop not found")
    complete_stop(db, stop, route)
    db.commit()
    return {"route": route_details(db, route)}


@router.post("/routes/{route_id}/complete")
def admin_complete_route(route_id: int, db: Session = Depends(get_db)):
    """Marks EVERY still-pending stop of this route as collected and closes the route.
    Same effect as the driver tapping 'completed' on each stop."""
    route = db.get(Route, route_id)
    if route is None:
        raise HTTPException(404, "Route not found")
    pending = db.scalars(
        select(CollectionStop).where(CollectionStop.route_id == route_id, CollectionStop.status == "pending")
    ).all()
    for stop in pending:
        complete_stop(db, stop, route)
    route.status = "done"
    db.commit()
    return {"route": route_details(db, route)}


@router.get("/summary")
def summary(db: Session = Depends(get_db)):
    """Numbers for the dashboard cards."""
    today = today_tz()
    period = today.strftime("%Y-%m")
    active_customers = select(Customer).join(User, User.id == Customer.user_id).where(User.is_active.is_(True))
    total = db.scalar(select(func.count()).select_from(active_customers.subquery())) or 0
    paid = db.scalar(
        select(func.count()).select_from(active_customers.where(Customer.payment_status == PaymentStatus.PAID).subquery())
    ) or 0
    revenue = db.scalar(
        select(func.coalesce(func.sum(Payment.amount), 0)).where(
            Payment.status == "completed", Payment.billing_period == period
        )
    )
    # Cost per household = today's total trip cost / households collected from today
    cost_today = db.scalar(select(func.coalesce(func.sum(Route.total_cost_tzs), 0)).where(Route.route_date == today))
    households_today = db.scalar(
        select(func.count(CollectionStop.id)).where(CollectionStop.stop_date == today, CollectionStop.customer_id.is_not(None))
    )
    in_operation = db.scalar(
        select(func.count(func.distinct(Route.truck_id))).where(Route.route_date == today, Route.status != "done")
    )
    return {
        "residents_total": total,
        "residents_paid": paid,
        "coverage_percent": round(100 * paid / total, 1) if total else 0.0,
        "revenue_tzs": revenue,
        "trucks_total": db.scalar(select(func.count(Truck.id))) or 0,
        "trucks_in_operation": in_operation or 0,
        "bins_total": db.scalar(select(func.count(WasteBin.id)).where(WasteBin.is_active.is_(True))) or 0,
        "cost_per_household_tzs": round(cost_today / households_today) if households_today else 0,
        "complaints": db.scalar(select(func.count(Complaint.id))) or 0,
    }


@router.get("/map")
def live_map(db: Session = Depends(get_db)):
    """Everything the live map shows: EVERY registered customer (colored by payment_status),
    all bins, and today's collection stops (so the frontend can grey out what's already collected)."""
    stops = db.scalars(
        select(CollectionStop)
        .where(or_(CollectionStop.stop_date == today_tz(), CollectionStop.status == "pending"))
        .order_by(CollectionStop.id)
    ).all()
    return {
        "depot": {"lat": settings.DEPOT_LATITUDE, "lng": settings.DEPOT_LONGITUDE},
        "customers": [
            CustomerOut.model_validate(c).model_dump()
            for c in db.scalars(select(Customer).join(User, User.id == Customer.user_id).where(User.is_active.is_(True)))
        ],
        "bins": [BinOut.model_validate(b).model_dump() for b in db.scalars(select(WasteBin).where(WasteBin.is_active.is_(True))).all()],
        "stops": [stop_dict(db, s) for s in stops],
    }
