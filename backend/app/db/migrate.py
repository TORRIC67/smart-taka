"""Tiny startup migration, so a new deploy never needs a manual database step.

Base.metadata.create_all() only creates tables that do not exist yet - it never adds a
column to a table that already exists. When a newer version of the app needs a new column,
ensure_columns() adds it (only if it is missing), on both PostgreSQL and SQLite.
"""
import logging

from sqlalchemy import inspect, select, text, update
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.customer import Customer
from app.models.fleet import Truck
from app.models.provider import ServiceProvider
from app.models.user import Role, User
from app.models.waste_bin import WasteBin

log = logging.getLogger("smarttaka.migrate")

# (table, column, column definition). Add a line here whenever a model gets a new column.
NEW_COLUMNS = [
    ("bins", "is_active", "BOOLEAN NOT NULL DEFAULT TRUE"),  # False = removed/relocated away
    ("routes", "geometry_json", "TEXT"),                     # road-following line for the map
    ("users", "provider_id", "INTEGER"),                     # the zone an admin/driver belongs to
    ("customers", "provider_id", "INTEGER"),
    ("bins", "provider_id", "INTEGER"),
    ("trucks", "provider_id", "INTEGER"),
    ("payments", "provider_id", "INTEGER"),
    ("users", "reset_otp_code", "VARCHAR(6)"),         # forgot-password OTP, cleared after use
    ("users", "reset_otp_expires_at", "TIMESTAMP"),
    ("customers", "wallet_balance_tzs", "INTEGER NOT NULL DEFAULT 0"),
    ("payments", "purpose", "VARCHAR(20) NOT NULL DEFAULT 'monthly_bill'"),
    ("customers", "category", "VARCHAR(20) NOT NULL DEFAULT 'residential'"),
    ("customers", "monthly_fee_tzs", "INTEGER"),  # NULL = standard fee for the zone
]


def ensure_columns(engine: Engine) -> None:
    inspector = inspect(engine)
    for table, column, definition in NEW_COLUMNS:
        if not inspector.has_table(table):
            continue  # brand-new database: create_all() already made it with every column
        if column in {c["name"] for c in inspector.get_columns(table)}:
            continue
        with engine.begin() as conn:
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {definition}"))
        log.warning("Migration: added column %s.%s", table, column)


def ensure_super_admin(db: Session) -> None:
    """There must always be one super admin (the only one who can add/remove other admins).
    If none exists - e.g. right after upgrading an older database where the first admin was
    just 'admin' - the earliest-created admin account becomes the super admin."""
    if db.scalar(select(User.id).where(User.role == Role.SUPER_ADMIN, User.is_active.is_(True))) is not None:
        return
    first = db.scalar(select(User).where(User.role == Role.ADMIN, User.is_active.is_(True)).order_by(User.id))
    if first is not None:
        first.role = Role.SUPER_ADMIN
        first.provider_id = None  # a super admin belongs to no single zone
        db.commit()
        log.warning("Migration: %s (%s) is now the super admin", first.full_name, first.phone)


def ensure_default_provider(db: Session) -> None:
    """This app used to be single-zone: one depot, one fuel price (from .env), everything
    else unscoped. The very first time this runs after upgrading, turn that single setup
    into the first ServiceProvider row, and attach every existing customer/bin/truck/admin
    that has no provider yet to it - so nothing that was already registered disappears."""
    if db.scalar(select(ServiceProvider.id)) is not None:
        return  # already migrated (or a fresh install that created its own providers)
    default = ServiceProvider(
        name="Dar es Salaam",
        depot_latitude=settings.DEPOT_LATITUDE,
        depot_longitude=settings.DEPOT_LONGITUDE,
        fuel_price_tzs_per_liter=settings.FUEL_PRICE_TZS_PER_LITER,
    )
    db.add(default)
    db.flush()
    db.execute(update(Customer).where(Customer.provider_id.is_(None)).values(provider_id=default.id))
    db.execute(update(WasteBin).where(WasteBin.provider_id.is_(None)).values(provider_id=default.id))
    db.execute(update(Truck).where(Truck.provider_id.is_(None)).values(provider_id=default.id))
    db.execute(
        update(User).where(User.provider_id.is_(None), User.role == Role.ADMIN).values(provider_id=default.id)
    )
    db.commit()
    log.warning("Migration: created default service provider %r and attached existing data to it", default.name)
