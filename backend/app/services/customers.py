"""Creating a customer = creating a login (User) + the household record (Customer).
Used by BOTH self-registration (/auth/register) and admin registration (/admin/customers)."""
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.customer import Customer
from app.models.user import Role, User
from app.schemas import CustomerCreate


def create_customer(
    db: Session, data: CustomerCreate, provider_id: int,
    category: str = "residential", monthly_fee_tzs: Optional[int] = None,
) -> Customer:
    """category/monthly_fee_tzs are explicit kwargs (not read off `data` here) on purpose:
    only the admin-registration endpoint passes them through. Self-registration and
    field-agent registration never do, so a caller can never set their own custom fee or
    mark themselves an 'institution', even if those fields are present in the request body."""
    user = User(
        full_name=data.full_name,
        phone=data.phone,
        password_hash=hash_password(data.password),
        role=Role.RESIDENT,
    )
    db.add(user)
    try:
        db.flush()  # gets user.id; also triggers the "phone already used" check
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "This phone number is already registered")

    customer = Customer(
        user_id=user.id,
        phone=data.phone,
        ward=data.ward,
        address=data.address,
        latitude=data.latitude,
        longitude=data.longitude,
        provider_id=provider_id,
        category=category,
        monthly_fee_tzs=monthly_fee_tzs,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer
