"""bins table - public bins fitted with an IoT fill-level sensor."""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class WasteBin(Base):
    __tablename__ = "bins"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)  # the sensor sends this ID
    ward: Mapped[str] = mapped_column(String(80), index=True)
    latitude: Mapped[float]
    longitude: Mapped[float]
    fill_level: Mapped[int] = mapped_column(default=0)          # last reading, 0-100 %
    status: Mapped[str] = mapped_column(String(10), default="ok")  # ok | full
    last_reading_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
