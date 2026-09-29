"""customers table - a household that pays for waste collection."""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.user import User


class PaymentStatus:
    REGISTERED = "registered"  # added to the system, not billed yet
    BILLED = "billed"          # billing SMS sent, waiting for payment
    PAID = "paid"              # paid -> appears on today's collection list


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    phone: Mapped[str] = mapped_column(String(20))  # number that receives SMS / pays (can differ from login later)
    ward: Mapped[str] = mapped_column(String(80), index=True)
    address: Mapped[Optional[str]] = mapped_column(String(255))
    latitude: Mapped[float]   # used by map display + route optimization
    longitude: Mapped[float]
    provider_id: Mapped[Optional[int]] = mapped_column(ForeignKey("providers.id"), nullable=True, index=True)
    payment_status: Mapped[str] = mapped_column(String(20), default=PaymentStatus.REGISTERED, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship()

    @property
    def full_name(self) -> str:
        return self.user.full_name

    @property
    def is_active(self) -> bool:
        return self.user.is_active
