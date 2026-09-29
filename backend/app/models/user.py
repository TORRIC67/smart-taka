"""users table - everyone who can log in (admin, resident, driver)."""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Role:
    SUPER_ADMIN = "super_admin"  # can also add/remove other admins - everything else is the same as ADMIN
    ADMIN = "admin"
    RESIDENT = "resident"
    DRIVER = "driver"
    ADMINS = (ADMIN, SUPER_ADMIN)  # everyone who may use the admin screens


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str] = mapped_column(String(20), unique=True, index=True)  # also the login name
    email: Mapped[Optional[str]] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), index=True)  # admin | super_admin | resident | driver
    is_active: Mapped[bool] = mapped_column(default=True)
    # The zone this admin/driver manages. NULL for a super admin (all zones) and for a resident
    # (a customer's zone lives on their Customer row instead, since one login could in theory
    # apply to either - in practice only admin/driver logins use this column).
    provider_id: Mapped[Optional[int]] = mapped_column(ForeignKey("providers.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
