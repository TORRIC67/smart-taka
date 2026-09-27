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
from app.routing.planner import stop_dict
from app.core.config import settings
from app.schemas import BinCreate, BinOut, CustomerCreate, CustomerOut, CustomerUpdate, DriverCreate
from app.services.billing import today_tz
from app.services.customers import create_customer

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_roles(Role.ADMIN))])


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
def list_bins(db: Session = Depends(get_db)):
    return db.scalars(select(WasteBin).order_by(WasteBin.id)).all()


@router.delete("/bins/{bin_id}")
def remove_bin(bin_id: int, db: Session = Depends(get_db)):
    """Removes a bin. Refused if it has ever been part of a route (so history stays intact) -
    in that case just leave it registered; a bin sitting idle costs nothing."""
    waste_bin = db.get(WasteBin, bin_id)
    if waste_bin is None:
        raise HTTPException(404, "Bin not found")
    used = db.scalar(select(func.count(CollectionStop.id)).where(CollectionStop.bin_id == bin_id))
    if used:
        raise HTTPException(409, "Bin haiwezi kufutwa kwa sababu tayari imeshawahi kuwa kwenye route.")
    db.delete(waste_bin)
    db.commit()
    return {"ok": True}


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
        "bins": [BinOut.model_validate(b).model_dump() for b in db.scalars(select(WasteBin)).all()],
        "stops": [stop_dict(db, s) for s in stops],
    }
