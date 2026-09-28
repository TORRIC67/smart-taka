"""IoT bin sensors send their fill level here.

A sensor (ESP32, GSM module, ...) does:
    POST /sensors/readings
    header  X-Sensor-Key: <SENSOR_API_KEY from .env>
    body    {"bin_code": "BIN-001", "fill_level": 85}      (latitude/longitude optional)

At or above BIN_FULL_THRESHOLD the bin is marked 'full' and added to the collection list.
"""
import hmac
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import settings
from app.models.route import CollectionStop
from app.models.waste_bin import WasteBin
from app.services.billing import today_tz

router = APIRouter(prefix="/sensors", tags=["sensors"])


class SensorReading(BaseModel):
    bin_code: str = Field(min_length=1, max_length=50)
    fill_level: int = Field(ge=0, le=100)  # percent
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)


@router.post("/readings")
def receive_reading(
    reading: SensorReading,
    x_sensor_key: str = Header(default=""),
    db: Session = Depends(get_db),
):
    if not settings.SENSOR_API_KEY:
        raise HTTPException(503, "Sensor endpoint is disabled: set SENSOR_API_KEY in .env")
    if not hmac.compare_digest(x_sensor_key.encode(), settings.SENSOR_API_KEY.encode()):
        raise HTTPException(401, "Invalid sensor key")

    waste_bin = db.scalar(select(WasteBin).where(WasteBin.code == reading.bin_code))
    if waste_bin is None:
        raise HTTPException(404, "Unknown bin_code - register the bin first")
    if not waste_bin.is_active:
        # Removed/relocated away by an admin: ignore its readings so it never lands on a route
        raise HTTPException(409, "This bin was removed from service")

    waste_bin.fill_level = reading.fill_level
    waste_bin.last_reading_at = datetime.now(timezone.utc)
    if reading.latitude is not None and reading.longitude is not None:
        waste_bin.latitude, waste_bin.longitude = reading.latitude, reading.longitude

    is_full = reading.fill_level >= settings.BIN_FULL_THRESHOLD
    waste_bin.status = "full" if is_full else "ok"

    added_to_list = False
    if is_full:
        # add to the collection list unless it is already waiting there
        waiting = db.scalar(
            select(CollectionStop).where(CollectionStop.bin_id == waste_bin.id, CollectionStop.status == "pending")
        )
        if waiting is None:
            db.add(CollectionStop(stop_date=today_tz(), bin_id=waste_bin.id))
            added_to_list = True

    db.commit()
    return {"bin_code": waste_bin.code, "fill_level": waste_bin.fill_level, "status": waste_bin.status,
            "added_to_collection_list": added_to_list}
