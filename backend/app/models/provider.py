"""providers table - one row per zone/region (e.g. a mkoa). Each has its own depot
location, fuel price, fleet, customers and bins. A regular admin belongs to exactly
one provider; a super admin belongs to none (they see every provider)."""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ServiceProvider(Base):
    __tablename__ = "providers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)  # e.g. "Dar es Salaam"
    depot_latitude: Mapped[float]   # where this zone's trucks start/end the day
    depot_longitude: Mapped[float]
    fuel_price_tzs_per_liter: Mapped[int] = mapped_column(Integer, default=3000)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
