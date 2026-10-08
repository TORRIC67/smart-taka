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


class CustomerCategory:
    RESIDENTIAL = "residential"   # a normal household - pays the zone's standard fee
    INSTITUTION = "institution"   # a company/school/large building - usually pays a custom fee


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
    category: Mapped[str] = mapped_column(String(20), default=CustomerCategory.RESIDENTIAL, index=True)
    # Null = pays the zone's standard MONTHLY_FEE_TZS. Set = this customer (e.g. a school,
    # company or large building) pays this exact amount instead - every billing path
    # (USSD push, wallet, SMS text) resolves through this.
    monthly_fee_tzs: Mapped[Optional[int]] = mapped_column(nullable=True)
    # Extra money the customer has pre-paid. Monthly bills can be paid from this
    # instead of a fresh mobile-money push; a top-up (or an overpayment) adds to it.
    wallet_balance_tzs: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship()

    @property
    def full_name(self) -> str:
        return self.user.full_name

    @property
    def is_active(self) -> bool:
        return self.user.is_active

    @property
    def effective_fee_tzs(self) -> int:
        """What this ONE customer actually owes per month - their own custom amount
        (set for e.g. a school or company) if any, otherwise the zone's standard fee."""
        from app.core.config import settings  # local import: avoids a import-time cycle

        return self.monthly_fee_tzs if self.monthly_fee_tzs else settings.MONTHLY_FEE_TZS
