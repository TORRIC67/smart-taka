"""Every webhook call from a payment provider is saved here BEFORE we act on it, so if
processing fails (or the token is wrong, or the payload is unexpected) there is always a
record of exactly what arrived and why it did or didn't get processed."""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class WebhookLog(Base):
    __tablename__ = "webhook_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(30))  # "harakapay"
    order_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    raw_payload: Mapped[str] = mapped_column(Text)
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
