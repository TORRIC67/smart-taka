"""Creating a customer = creating a login (User) + the household record (Customer).
Used by BOTH self-registration (/auth/register) and admin registration (/admin/customers)."""
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.customer import Customer
from app.models.user import Role, User
from app.schemas import CustomerCreate


def create_customer(db: Session, data: CustomerCreate) -> Customer:
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
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer
