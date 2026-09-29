"""Login, self-registration (residents) and 'who am I'."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.core.phone import normalize_phone
from app.core.security import create_access_token, verify_password
from app.models.customer import Customer
from app.models.provider import ServiceProvider
from app.models.user import User
from app.schemas import CustomerCreate, CustomerOut, TokenOut
from app.services.customers import create_customer

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenOut)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Log in with phone number (as 'username') and password."""
    try:
        phone = normalize_phone(form.username)
    except ValueError:
        phone = form.username
    user = db.scalar(select(User).where(User.phone == phone))
    if user is None or not user.is_active or not verify_password(form.password, user.password_hash):
        raise HTTPException(401, "Wrong phone number or password")
    return {"access_token": create_access_token(user.id, user.role)}


@router.post("/register", response_model=CustomerOut, status_code=201)
def self_register(data: CustomerCreate, db: Session = Depends(get_db)):
    """Optional self-registration: a resident signs up on their own. Role is always 'resident'.
    They must say which zone/provider they belong to (an admin-created customer instead
    gets this automatically from the admin who registers them)."""
    if data.provider_id is None:
        raise HTTPException(400, "provider_id is required")
    provider = db.get(ServiceProvider, data.provider_id)
    if provider is None or not provider.is_active:
        raise HTTPException(404, "Service provider not found")
    return create_customer(db, data, provider_id=provider.id)


@router.get("/me")
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """The frontend calls this after login. residents get their customer_id (needed for the Pay button)."""
    customer = db.scalar(select(Customer).where(Customer.user_id == user.id))
    return {
        "id": user.id,
        "full_name": user.full_name,
        "phone": user.phone,
        "role": user.role,
        "customer_id": customer.id if customer else None,
        "customer": CustomerOut.model_validate(customer).model_dump() if customer else None,
        "monthly_fee_tzs": settings.MONTHLY_FEE_TZS,
    }
