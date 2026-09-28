"""Tiny startup migration, so a new deploy never needs a manual database step.

Base.metadata.create_all() only creates tables that do not exist yet - it never adds a
column to a table that already exists. When a newer version of the app needs a new column,
ensure_columns() adds it (only if it is missing), on both PostgreSQL and SQLite.
"""
import logging

from sqlalchemy import inspect, select, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.models.user import Role, User

log = logging.getLogger("smarttaka.migrate")

# (table, column, column definition). Add a line here whenever a model gets a new column.
NEW_COLUMNS = [
    ("bins", "is_active", "BOOLEAN NOT NULL DEFAULT TRUE"),  # False = removed/relocated away
    ("routes", "geometry_json", "TEXT"),                     # road-following line for the map
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
        db.commit()
        log.warning("Migration: %s (%s) is now the super admin", first.full_name, first.phone)
