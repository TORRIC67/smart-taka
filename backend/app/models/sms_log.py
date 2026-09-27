"""sms_logs table - every SMS we try to send (so admin can see what went out and what failed)."""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SmsLog(Base):
    __tablename__ = "sms_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    period: Mapped[str] = mapped_column(String(7), index=True)  # billing month, e.g. "2026-09"
    kind: Mapped[str] = mapped_column(String(20), default="billing")
    phone: Mapped[str] = mapped_column(String(20))
    message: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(10))  # ok | failed
    error: Mapped[Optional[str]] = mapped_column(String(300))
    provider_ref: Mapped[Optional[str]] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
