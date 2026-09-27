"""Request/response shapes (what the frontend sends and receives). Pydantic validates them for us."""
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.phone import normalize_phone


class _WithPhone(BaseModel):
    phone: str

    @field_validator("phone")
    @classmethod
    def _clean_phone(cls, v: str) -> str:
        return normalize_phone(v)  # ValueError becomes a clear 422 message for the client


class CustomerCreate(_WithPhone):
    full_name: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=8, max_length=72)  # bcrypt only reads the first 72 bytes
    ward: str = Field(min_length=1, max_length=80)
    address: Optional[str] = Field(default=None, max_length=255)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class CustomerUpdate(BaseModel):
    """Every field is optional: send only what changed. Password is not editable here -
    add a separate 'reset password' action later if you need that."""
    full_name: Optional[str] = Field(default=None, min_length=2, max_length=120)
    phone: Optional[str] = None
    ward: Optional[str] = Field(default=None, min_length=1, max_length=80)
    address: Optional[str] = Field(default=None, max_length=255)
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)

    @field_validator("phone")
    @classmethod
    def _clean_phone(cls, v):
        return normalize_phone(v) if v else v


class DriverCreate(_WithPhone):
    full_name: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=8, max_length=72)
    plate_number: str = Field(min_length=3, max_length=20)
    fuel_km_per_liter: float = Field(gt=0)  # truck fuel efficiency, used for trip cost


class BinCreate(BaseModel):
    code: str = Field(min_length=1, max_length=50)  # the ID the sensor will send
    ward: str = Field(min_length=1, max_length=80)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class ComplaintCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    message: str = Field(min_length=1, max_length=1000)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CustomerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    phone: str
    ward: str
    address: Optional[str]
    latitude: float
    longitude: float
    payment_status: str
    is_active: bool = True


class BinOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    ward: str
    latitude: float
    longitude: float
    fill_level: int
    status: str
