"""Admin-only endpoints: register users/bins, see customers and dashboard numbers.
The dependency on the router itself locks EVERY endpoint here to role 'admin'/'super_admin'.

Zone (Service Provider) scoping: a regular admin only ever sees/touches their own zone's
data - enforced by get_optional_scope()/get_required_provider() and the ownership checks
below. A super admin sees everything, or one zone at a time via ?provider_id=."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_optional_scope, get_required_provider, require_roles
from app.core.security import hash_password
from app.models.complaint import Complaint
from app.models.customer import Customer, PaymentStatus
from app.models.fleet import Driver, Truck
from app.models.payment import Payment
from app.models.provider import ServiceProvider
from app.models.route import CollectionStop, Route
from app.models.user import Role, User
from app.models.waste_bin import WasteBin
from app.models.webhook_log import WebhookLog
from app.routing.planner import complete_stop, route_details, stop_dict
from app.schemas import (
    AdminCreate, AdminOut, BinCreate, BinOut, BinUpdate, CustomerCreate, CustomerOut,
    CustomerUpdate, DriverCreate, DriverOut, PaymentHistoryOut, ProviderCreate, ProviderOut,
    ProviderUpdate,
)
from app.services.billing import today_tz
from app.services.customers import create_customer
from app.services.reports_pdf import build_collections_report_pdf, build_customer_statement_pdf

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_roles(*Role.ADMINS))])
super_admin_only = Depends(require_roles(Role.SUPER_ADMIN))


def _resolve_creation_provider(user: User, requested_provider_id: Optional[int], db: Session) -> int:
    """Which zone a newly-registered customer/bin/driver belongs to. A regular admin always
    uses their own zone (the request can't override that). A super admin must say which
    zone explicitly, since they don't run day-to-day operations in any one zone."""
    if user.role == Role.SUPER_ADMIN:
        if requested_provider_id is None:
            raise HTTPException(400, "provider_id is required when a super admin registers this directly")
        if db.get(ServiceProvider, requested_provider_id) is None:
            raise HTTPException(404, "Service provider not found")
        return requested_provider_id
    return user.provider_id


# ---------- registering things ----------
@router.post("/customers", response_model=CustomerOut, status_code=201)
def register_customer(data: CustomerCreate, user: User = Depends(require_roles(*Role.ADMINS)), db: Session = Depends(get_db)):
    provider_id = _resolve_creation_provider(user, data.provider_id, db)
    return create_customer(db, data, provider_id)


@router.post("/drivers", status_code=201)
def register_driver(data: DriverCreate, user: User = Depends(require_roles(*Role.ADMINS)), db: Session = Depends(get_db)):
    """Creates the driver's login AND their truck (in this zone) in one step."""
    provider_id = _resolve_creation_provider(user, data.provider_id, db)
    driver_user = User(
        full_name=data.full_name,
        phone=data.phone,
        password_hash=hash_password(data.password),
        role=Role.DRIVER,
        provider_id=provider_id,
    )
    db.add(driver_user)
    try:
        db.flush()
        driver = Driver(user_id=driver_user.id)
        db.add(driver)
        db.flush()
        truck = Truck(
            plate_number=data.plate_number, driver_id=driver.id,
            fuel_km_per_liter=data.fuel_km_per_liter, provider_id=provider_id,
        )
        db.add(truck)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Phone number or plate number is already registered")
    return {"driver_id": driver.id, "truck_id": truck.id, "plate_number": truck.plate_number}


@router.delete("/drivers/{driver_id}")
def remove_driver(driver_id: int, scope: Optional[int] = Depends(get_optional_scope), db: Session = Depends(get_db)):
    """Removes a driver: their login is disabled and their truck is taken out of routing.
    A route already generated today is left alone; regenerate routes after removing a driver."""
    driver = db.get(Driver, driver_id)
    driver_user = db.get(User, driver.user_id) if driver else None
    if driver is None or driver_user is None or (scope is not None and driver_user.provider_id != scope):
        raise HTTPException(404, "Driver not found")
    driver_user.is_active = False
    for truck in db.scalars(select(Truck).where(Truck.driver_id == driver_id)):
        truck.is_active = False
    db.commit()
    return {"ok": True}


@router.post("/bins", response_model=BinOut, status_code=201)
def register_bin(data: BinCreate, user: User = Depends(require_roles(*Role.ADMINS)), db: Session = Depends(get_db)):
    provider_id = _resolve_creation_provider(user, data.provider_id, db)
    waste_bin = WasteBin(code=data.code, ward=data.ward, latitude=data.latitude, longitude=data.longitude, provider_id=provider_id)
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
    """Creates a new (regular) admin login FOR ONE ZONE. Only a super admin can do this - a
    regular admin can do everything else here except add or remove other admins."""
    if db.get(ServiceProvider, data.provider_id) is None:
        raise HTTPException(404, "Service provider not found")
    user = User(
        full_name=data.full_name, phone=data.phone, password_hash=hash_password(data.password),
        role=Role.ADMIN, provider_id=data.provider_id,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Phone number is already registered")
    db.refresh(user)
    return _admin_out(db, user)


def _admin_out(db: Session, user: User) -> AdminOut:
    provider = db.get(ServiceProvider, user.provider_id) if user.provider_id else None
    return AdminOut(
        id=user.id, full_name=user.full_name, phone=user.phone, role=user.role, is_active=user.is_active,
        provider_id=user.provider_id, provider_name=provider.name if provider else None,
    )


@router.get("/admins", response_model=List[AdminOut], dependencies=[super_admin_only])
def list_admins(db: Session = Depends(get_db)):
    rows = db.scalars(select(User).where(User.role.in_([Role.ADMIN, Role.SUPER_ADMIN])).order_by(User.id)).all()
    return [_admin_out(db, u) for u in rows]


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
    return _admin_out(db, target)


@router.post("/admins/{admin_id}/reactivate", response_model=AdminOut, dependencies=[super_admin_only])
def reactivate_admin(admin_id: int, db: Session = Depends(get_db)):
    target = db.get(User, admin_id)
    if target is None or target.role not in (Role.ADMIN, Role.SUPER_ADMIN):
        raise HTTPException(404, "Admin not found")
    target.is_active = True
    db.commit()
    db.refresh(target)
    return _admin_out(db, target)


# ---------- service providers (zones) - super admin only ----------
def _provider_out(db: Session, p: ServiceProvider) -> ProviderOut:
    period = today_tz().strftime("%Y-%m")
    customers_total = db.scalar(
        select(func.count(Customer.id)).join(User, User.id == Customer.user_id)
        .where(Customer.provider_id == p.id, User.is_active.is_(True))
    ) or 0
    bins_total = db.scalar(select(func.count(WasteBin.id)).where(WasteBin.provider_id == p.id, WasteBin.is_active.is_(True))) or 0
    trucks_total = db.scalar(select(func.count(Truck.id)).where(Truck.provider_id == p.id, Truck.is_active.is_(True))) or 0
    revenue = db.scalar(
        select(func.coalesce(func.sum(Payment.amount), 0)).where(
            Payment.provider_id == p.id, Payment.status == "completed", Payment.billing_period == period
        )
    ) or 0
    return ProviderOut(
        id=p.id, name=p.name, depot_latitude=p.depot_latitude, depot_longitude=p.depot_longitude,
        fuel_price_tzs_per_liter=p.fuel_price_tzs_per_liter, is_active=p.is_active,
        customers_total=customers_total, bins_total=bins_total, trucks_total=trucks_total,
        revenue_this_month_tzs=revenue,
    )


@router.post("/providers", response_model=ProviderOut, status_code=201, dependencies=[super_admin_only])
def create_provider(data: ProviderCreate, db: Session = Depends(get_db)):
    """A new zone/region. Register its first admin afterwards with POST /admin/admins."""
    provider = ServiceProvider(
        name=data.name, depot_latitude=data.depot_latitude, depot_longitude=data.depot_longitude,
        fuel_price_tzs_per_liter=data.fuel_price_tzs_per_liter,
    )
    db.add(provider)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "A service provider with this name already exists")
    db.refresh(provider)
    return _provider_out(db, provider)


@router.get("/providers", response_model=List[ProviderOut], dependencies=[super_admin_only])
def list_providers(db: Session = Depends(get_db)):
    rows = db.scalars(select(ServiceProvider).order_by(ServiceProvider.name)).all()
    return [_provider_out(db, p) for p in rows]


@router.get("/providers/mine", response_model=ProviderOut)
def my_provider(user: User = Depends(require_roles(*Role.ADMINS)), db: Session = Depends(get_db)):
    """A regular admin's own zone (so they can see/edit e.g. their own fuel price without
    needing the super-admin-only provider list)."""
    if user.provider_id is None:
        raise HTTPException(400, "This account has no zone assigned")
    return _provider_out(db, db.get(ServiceProvider, user.provider_id))


@router.patch("/providers/{provider_id}", response_model=ProviderOut)
def update_provider(
    provider_id: int, data: ProviderUpdate,
    user: User = Depends(require_roles(*Role.ADMINS)), db: Session = Depends(get_db),
):
    """Change a zone's fuel price (and/or depot location). A regular admin may only touch
    their own zone; a super admin may edit any zone."""
    if user.role != Role.SUPER_ADMIN and user.provider_id != provider_id:
        raise HTTPException(404, "Service provider not found")
    provider = db.get(ServiceProvider, provider_id)
    if provider is None:
        raise HTTPException(404, "Service provider not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(provider, field, value)
    db.commit()
    return _provider_out(db, provider)


# ---------- drivers/trucks (view) ----------
@router.get("/drivers", response_model=List[DriverOut])
def list_drivers(scope: Optional[int] = Depends(get_optional_scope), db: Session = Depends(get_db)):
    q = select(Driver, User, Truck).join(User, User.id == Driver.user_id).join(Truck, Truck.driver_id == Driver.id)
    if scope is not None:
        q = q.where(Truck.provider_id == scope)
    rows = db.execute(q.order_by(Driver.id)).all()
    provider_names = {p.id: p.name for p in db.scalars(select(ServiceProvider))}
    return [
        DriverOut(
            driver_id=driver.id, user_id=user.id, full_name=user.full_name, phone=user.phone,
            plate_number=truck.plate_number, fuel_km_per_liter=truck.fuel_km_per_liter, is_active=user.is_active,
            provider_id=truck.provider_id, provider_name=provider_names.get(truck.provider_id, "?"),
        )
        for driver, user, truck in rows
    ]


# ---------- viewing things ----------
@router.get("/customers", response_model=List[CustomerOut])
def list_customers(
    ward: Optional[str] = None,
    status: Optional[str] = None,  # registered | billed | paid
    include_inactive: bool = False,  # True = also show customers that were removed
    scope: Optional[int] = Depends(get_optional_scope),
    db: Session = Depends(get_db),
):
    q = select(Customer).join(User, User.id == Customer.user_id)
    if not include_inactive:
        q = q.where(User.is_active.is_(True))
    if scope is not None:
        q = q.where(Customer.provider_id == scope)
    if ward:
        q = q.where(Customer.ward == ward)
    if status:
        q = q.where(Customer.payment_status == status)
    return db.scalars(q.order_by(Customer.id)).all()


def _owned_customer(db: Session, customer_id: int, scope: Optional[int]) -> Customer:
    customer = db.get(Customer, customer_id)
    if customer is None or (scope is not None and customer.provider_id != scope):
        raise HTTPException(404, "Customer not found")
    return customer


@router.patch("/customers/{customer_id}", response_model=CustomerOut)
def update_customer(
    customer_id: int, data: CustomerUpdate,
    scope: Optional[int] = Depends(get_optional_scope), db: Session = Depends(get_db),
):
    """Edits a customer's own details (name, phone, ward, address, location). Send only the
    fields that changed. Password and payment_status are not editable here."""
    customer = _owned_customer(db, customer_id, scope)

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
def remove_customer(customer_id: int, scope: Optional[int] = Depends(get_optional_scope), db: Session = Depends(get_db)):
    """Removes a customer from the system: they can no longer log in, they disappear from the
    live map and from future collection lists and billing runs. Their payment and complaint
    history is kept (not deleted), in case you need it later - that's why this deactivates
    the account instead of erasing the row."""
    customer = _owned_customer(db, customer_id, scope)
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
def reactivate_customer(customer_id: int, scope: Optional[int] = Depends(get_optional_scope), db: Session = Depends(get_db)):
    """Undo a removal: the customer can log in again and reappears on the map."""
    customer = _owned_customer(db, customer_id, scope)
    customer.user.is_active = True
    db.commit()
    db.refresh(customer)
    return customer


@router.get("/customers/{customer_id}/payments", response_model=List[PaymentHistoryOut])
def customer_payment_history(customer_id: int, scope: Optional[int] = Depends(get_optional_scope), db: Session = Depends(get_db)):
    """One customer's full payment history - so an admin can look up a specific household."""
    _owned_customer(db, customer_id, scope)
    return db.scalars(select(Payment).where(Payment.customer_id == customer_id).order_by(Payment.created_at.desc())).all()


@router.get("/customers/{customer_id}/payments/pdf")
def customer_payment_history_pdf(customer_id: int, scope: Optional[int] = Depends(get_optional_scope), db: Session = Depends(get_db)):
    """Downloadable/printable statement for one customer (their full payment history)."""
    customer = _owned_customer(db, customer_id, scope)
    payments = db.scalars(select(Payment).where(Payment.customer_id == customer_id).order_by(Payment.created_at.desc())).all()
    zone = db.get(ServiceProvider, customer.provider_id) if customer.provider_id else None
    pdf_bytes = build_customer_statement_pdf(customer, payments, zone.name if zone else "-")
    return Response(
        content=pdf_bytes, media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="statement-{customer.id}.pdf"'},
    )


@router.get("/bins", response_model=List[BinOut])
def list_bins(include_inactive: bool = False, scope: Optional[int] = Depends(get_optional_scope), db: Session = Depends(get_db)):
    q = select(WasteBin)
    if not include_inactive:
        q = q.where(WasteBin.is_active.is_(True))
    if scope is not None:
        q = q.where(WasteBin.provider_id == scope)
    return db.scalars(q.order_by(WasteBin.id)).all()


def _owned_bin(db: Session, bin_id: int, scope: Optional[int]) -> WasteBin:
    waste_bin = db.get(WasteBin, bin_id)
    if waste_bin is None or (scope is not None and waste_bin.provider_id != scope):
        raise HTTPException(404, "Bin not found")
    return waste_bin


@router.patch("/bins/{bin_id}", response_model=BinOut)
def update_bin(bin_id: int, data: BinUpdate, scope: Optional[int] = Depends(get_optional_scope), db: Session = Depends(get_db)):
    """Edit a bin's details - typically its location after it has been physically moved.
    Send only the fields that changed."""
    waste_bin = _owned_bin(db, bin_id, scope)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(waste_bin, field, value)
    db.commit()
    db.refresh(waste_bin)
    return waste_bin


@router.delete("/bins/{bin_id}", response_model=BinOut)
def remove_bin(bin_id: int, scope: Optional[int] = Depends(get_optional_scope), db: Session = Depends(get_db)):
    """Takes a bin out of service (e.g. it was removed/relocated). History (any past
    collection stops) is kept - this only hides it from new routes and the live map."""
    waste_bin = _owned_bin(db, bin_id, scope)
    waste_bin.is_active = False
    for stop in db.scalars(
        select(CollectionStop).where(CollectionStop.bin_id == bin_id, CollectionStop.status == "pending")
    ):
        db.delete(stop)
    db.commit()
    db.refresh(waste_bin)
    return waste_bin


@router.post("/bins/{bin_id}/reactivate", response_model=BinOut)
def reactivate_bin(bin_id: int, scope: Optional[int] = Depends(get_optional_scope), db: Session = Depends(get_db)):
    waste_bin = _owned_bin(db, bin_id, scope)
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
def admin_complete_stop(stop_id: int, scope: Optional[int] = Depends(get_optional_scope), db: Session = Depends(get_db)):
    """Marks one stop as collected - the same action a driver does from their phone,
    available here too in case the driver can't (no phone, sensor found it already emptied,
    correcting a mistake, etc). A route finishes automatically once every one of its stops
    is marked complete this way or by the driver."""
    stop = db.get(CollectionStop, stop_id)
    route = db.get(Route, stop.route_id) if stop and stop.route_id else None
    truck = db.get(Truck, route.truck_id) if route else None
    if route is None or truck is None or (scope is not None and truck.provider_id != scope):
        raise HTTPException(404, "Stop not found")
    complete_stop(db, stop, route)
    db.commit()
    return {"route": route_details(db, route)}


@router.post("/routes/{route_id}/complete")
def admin_complete_route(route_id: int, scope: Optional[int] = Depends(get_optional_scope), db: Session = Depends(get_db)):
    """Marks EVERY still-pending stop of this route as collected and closes the route.
    Same effect as the driver tapping 'completed' on each stop."""
    route = db.get(Route, route_id)
    truck = db.get(Truck, route.truck_id) if route else None
    if route is None or truck is None or (scope is not None and truck.provider_id != scope):
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
def summary(scope: Optional[int] = Depends(get_optional_scope), db: Session = Depends(get_db)):
    """Numbers for the dashboard cards."""
    today = today_tz()
    period = today.strftime("%Y-%m")
    active_customers = select(Customer).join(User, User.id == Customer.user_id).where(User.is_active.is_(True))
    trucks_q = select(Truck)
    bins_q = select(WasteBin).where(WasteBin.is_active.is_(True))
    revenue_q = select(func.coalesce(func.sum(Payment.amount), 0)).where(
        Payment.status == "completed", Payment.billing_period == period
    )
    routes_cost_q = select(func.coalesce(func.sum(Route.total_cost_tzs), 0)).where(Route.route_date == today)
    households_q = select(func.count(CollectionStop.id)).where(
        CollectionStop.stop_date == today, CollectionStop.customer_id.is_not(None)
    )
    in_operation_q = select(func.count(func.distinct(Route.truck_id))).where(Route.route_date == today, Route.status != "done")
    if scope is not None:
        active_customers = active_customers.where(Customer.provider_id == scope)
        trucks_q = trucks_q.where(Truck.provider_id == scope)
        bins_q = bins_q.where(WasteBin.provider_id == scope)
        revenue_q = revenue_q.where(Payment.provider_id == scope)
        routes_cost_q = routes_cost_q.join(Truck, Truck.id == Route.truck_id).where(Truck.provider_id == scope)
        households_q = households_q.join(Customer, Customer.id == CollectionStop.customer_id).where(Customer.provider_id == scope)
        in_operation_q = in_operation_q.join(Truck, Truck.id == Route.truck_id).where(Truck.provider_id == scope)

    total = db.scalar(select(func.count()).select_from(active_customers.subquery())) or 0
    paid = db.scalar(
        select(func.count()).select_from(active_customers.where(Customer.payment_status == PaymentStatus.PAID).subquery())
    ) or 0
    revenue = db.scalar(revenue_q)
    cost_today = db.scalar(routes_cost_q)
    households_today = db.scalar(households_q)
    in_operation = db.scalar(in_operation_q)
    complaints_q = select(func.count(Complaint.id))
    if scope is not None:
        complaints_q = complaints_q.join(Customer, Customer.id == Complaint.customer_id).where(Customer.provider_id == scope)
    return {
        "residents_total": total,
        "residents_paid": paid,
        "coverage_percent": round(100 * paid / total, 1) if total else 0.0,
        "revenue_tzs": revenue,
        "trucks_total": db.scalar(select(func.count()).select_from(trucks_q.subquery())) or 0,
        "trucks_in_operation": in_operation or 0,
        "bins_total": db.scalar(select(func.count()).select_from(bins_q.subquery())) or 0,
        "cost_per_household_tzs": round(cost_today / households_today) if households_today else 0,
        "complaints": db.scalar(complaints_q) or 0,
    }


@router.get("/map")
def live_map(provider: ServiceProvider = Depends(get_required_provider), db: Session = Depends(get_db)):
    """Everything the live map shows: EVERY registered customer (colored by payment_status),
    all bins, and today's collection stops (so the frontend can grey out what's already collected).
    Scoped to one zone - a super admin must pick one with ?provider_id=."""
    stops = db.scalars(
        select(CollectionStop)
        .where(or_(CollectionStop.stop_date == today_tz(), CollectionStop.status == "pending"))
        .order_by(CollectionStop.id)
    ).all()
    customers = db.scalars(
        select(Customer).join(User, User.id == Customer.user_id)
        .where(User.is_active.is_(True), Customer.provider_id == provider.id)
    ).all()
    bins = db.scalars(select(WasteBin).where(WasteBin.is_active.is_(True), WasteBin.provider_id == provider.id)).all()
    bin_ids, customer_ids = {b.id for b in bins}, {c.id for c in customers}
    return {
        "depot": {"lat": provider.depot_latitude, "lng": provider.depot_longitude},
        "customers": [CustomerOut.model_validate(c).model_dump() for c in customers],
        "bins": [BinOut.model_validate(b).model_dump() for b in bins],
        "stops": [stop_dict(db, s) for s in stops if (s.customer_id in customer_ids) or (s.bin_id in bin_ids)],
    }


# ---------- money reports: monthly / quarterly / annual, per zone and system-wide ----------
def _collections_report_data(granularity: str, scope: Optional[int], db: Session) -> dict:
    if granularity not in ("month", "quarter", "year"):
        raise HTTPException(400, "granularity must be month, quarter or year")

    q = select(Payment.billing_period, Payment.amount).where(Payment.status == "completed", Payment.purpose == "monthly_bill")
    if scope is not None:
        q = q.where(Payment.provider_id == scope)
    buckets: dict[str, dict] = {}
    for period, amount in db.execute(q).all():
        year, month = period.split("-")
        if granularity == "month":
            key = period
        elif granularity == "quarter":
            key = f"{year}-Q{(int(month) - 1) // 3 + 1}"
        else:
            key = year
        b = buckets.setdefault(key, {"period": key, "amount_tzs": 0, "payments_count": 0})
        b["amount_tzs"] += amount
        b["payments_count"] += 1
    rows = sorted(buckets.values(), key=lambda r: r["period"])

    result = {"granularity": granularity, "provider_id": scope, "rows": rows}
    if scope is None:  # super admin looking at everything: add a per-zone breakdown too
        pq = (
            select(ServiceProvider.id, ServiceProvider.name, func.coalesce(func.sum(Payment.amount), 0))
            .select_from(ServiceProvider)
            .outerjoin(Payment, (Payment.provider_id == ServiceProvider.id) & (Payment.status == "completed") & (Payment.purpose == "monthly_bill"))
            .group_by(ServiceProvider.id, ServiceProvider.name)
            .order_by(ServiceProvider.name)
        )
        result["by_provider"] = [
            {"provider_id": pid, "name": name, "total_tzs": total} for pid, name, total in db.execute(pq).all()
        ]
    return result


@router.get("/reports/collections")
def collections_report(
    granularity: str = "month",  # month | quarter | year
    scope: Optional[int] = Depends(get_optional_scope),
    db: Session = Depends(get_db),
):
    return _collections_report_data(granularity, scope, db)


@router.get("/reports/collections/pdf")
def collections_report_pdf(
    granularity: str = "month",
    scope: Optional[int] = Depends(get_optional_scope),
    db: Session = Depends(get_db),
):
    """Downloadable/printable PDF of the same report - one zone's, or every zone's for a
    super admin. Opens in the browser's own PDF viewer, which can print it directly."""
    data = _collections_report_data(granularity, scope, db)
    if scope is None:
        zone_name = "All zones"
    else:
        zone = db.get(ServiceProvider, scope)
        zone_name = zone.name if zone else "-"
    pdf_bytes = build_collections_report_pdf(data["rows"], granularity, zone_name, data.get("by_provider"))
    return Response(
        content=pdf_bytes, media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="collections-{granularity}.pdf"'},
    )


# ---------- webhook debugging (super admin only: this is raw technical data, not zone data) ----------
@router.get("/webhook-logs", dependencies=[super_admin_only])
def webhook_logs(limit: int = 50, db: Session = Depends(get_db)):
    rows = db.scalars(select(WebhookLog).order_by(WebhookLog.id.desc()).limit(min(limit, 200))).all()
    return [
        {
            "id": r.id, "source": r.source, "order_id": r.order_id, "processed": r.processed,
            "error": r.error, "created_at": r.created_at, "raw_payload": r.raw_payload[:1000],
        }
        for r in rows
    ]
