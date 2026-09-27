"""drivers + trucks tables."""
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Driver(Base):
    __tablename__ = "drivers"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)


class Truck(Base):
    __tablename__ = "trucks"

    id: Mapped[int] = mapped_column(primary_key=True)
    plate_number: Mapped[str] = mapped_column(String(20), unique=True)
    driver_id: Mapped[int] = mapped_column(ForeignKey("drivers.id"), index=True)
    # Needed by the route engine to turn distance into litres of fuel and then into TZS.
    fuel_km_per_liter: Mapped[float]
    is_active: Mapped[bool] = mapped_column(default=True)
