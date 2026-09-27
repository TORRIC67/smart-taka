"""routes + collection_stops tables.

collection_stops = the list of places to visit on a given day (paid customers + full bins).
routes           = the result of the AI route engine for one truck on one day.
"""
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Route(Base):
    __tablename__ = "routes"

    id: Mapped[int] = mapped_column(primary_key=True)
    truck_id: Mapped[int] = mapped_column(ForeignKey("trucks.id"), index=True)
    route_date: Mapped[date] = mapped_column(Date, index=True)
    total_distance_km: Mapped[Optional[float]]
    est_minutes: Mapped[Optional[int]]
    fuel_liters: Mapped[Optional[float]]
    total_cost_tzs: Mapped[Optional[int]]
    status: Mapped[str] = mapped_column(String(20), default="planned")  # planned | in_progress | done


class CollectionStop(Base):
    __tablename__ = "collection_stops"

    id: Mapped[int] = mapped_column(primary_key=True)
    stop_date: Mapped[date] = mapped_column(Date, index=True)
    # Exactly one of these two is filled: a paid customer OR a full bin.
    customer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("customers.id"), index=True)
    bin_id: Mapped[Optional[int]] = mapped_column(ForeignKey("bins.id"), index=True)
    route_id: Mapped[Optional[int]] = mapped_column(ForeignKey("routes.id"))
    sequence: Mapped[Optional[int]]  # order in the optimized route
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending | completed
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
