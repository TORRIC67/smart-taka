"""`payments` table - replaces the earlier "payments-placeholder" table.

One row = one payment attempt. A customer can have several attempts for the
same month (e.g. first one failed), but only one should end up 'completed'.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base  # <- adjust to wherever your declarative Base lives


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    # Copied from the customer at payment time, so zone reports stay correct even if a
    # customer is ever moved to a different provider later.
    provider_id: Mapped[Optional[int]] = mapped_column(ForeignKey("providers.id"), nullable=True, index=True)
    provider: Mapped[str] = mapped_column(String(30), default="harakapay")
    order_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)  # HarakaPay order_id
    phone: Mapped[str] = mapped_column(String(20))
    billing_period: Mapped[str] = mapped_column(String(7), index=True)  # e.g. "2026-09"

    # Money in whole TZS. We store what HarakaPay reports instead of calculating
    # the fee ourselves (see note about 5.9% vs 6% in the docs).
    amount: Mapped[int]
    fee: Mapped[int] = mapped_column(default=0)
    net_amount: Mapped[int] = mapped_column(default=0)

    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
