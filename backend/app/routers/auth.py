"""Login, self-registration (residents), password self-service, and 'who am I'."""
import random
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.core.phone import normalize_phone
from app.core.security import create_access_token, hash_password, verify_password
from app.models.customer import Customer
from app.models.provider import ServiceProvider
from app.models.user import User
from app.schemas import (
    ChangePasswordRequest, CustomerCreate, CustomerOut, ForgotPasswordRequest,
    ResetPasswordRequest, TokenOut,
)
from app.services.customers import create_customer
from app.sms.service import get_sms_provider

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
        "monthly_fee_tzs": customer.effective_fee_tzs if customer else settings.MONTHLY_FEE_TZS,
    }


# ---------- password: change (logged in) and forgot/reset (via SMS code) ----------
@router.post("/change-password")
def change_password(data: ChangePasswordRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Any logged-in user (customer, admin or super admin) changes their own password."""
    if not verify_password(data.current_password, user.password_hash):
        raise HTTPException(401, "Current password is wrong")
    user.password_hash = hash_password(data.new_password)
    db.commit()
    return {"ok": True}


@router.post("/forgot-password")
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Texts a 6-digit code to the phone on file, valid for 10 minutes. Always answers the
    same way whether or not that phone is registered, so this can't be used to check who
    has an account."""
    try:
        phone = normalize_phone(data.phone)
    except ValueError:
        phone = data.phone
    user = db.scalar(select(User).where(User.phone == phone, User.is_active.is_(True)))
    if user is not None:
        code = f"{random.randint(0, 999999):06d}"
        user.reset_otp_code = code
        user.reset_otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        db.commit()
        try:
            get_sms_provider().send(phone, f"Smart Taka: Msimbo wako wa kubadili password ni {code}. Ni halali kwa dakika 10 tu.")
        except RuntimeError:
            pass  # SMS not configured in this environment - the code still works if support reads it from the DB
    return {"ok": True, "message": "If that phone number is registered, a code has been sent to it."}


@router.post("/reset-password")
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    try:
        phone = normalize_phone(data.phone)
    except ValueError:
        phone = data.phone
    user = db.scalar(select(User).where(User.phone == phone, User.is_active.is_(True)))
    if user is None or user.reset_otp_code is None or user.reset_otp_code != data.otp_code:
        raise HTTPException(400, "That code is wrong or has expired")
    expires_at = user.reset_otp_expires_at
    if expires_at is not None and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)  # SQLite drops tzinfo on the way back
    if expires_at is None or expires_at < datetime.now(timezone.utc):
        raise HTTPException(400, "That code is wrong or has expired")
        raise HTTPException(400, "That code is wrong or has expired")
    user.password_hash = hash_password(data.new_password)
    user.reset_otp_code = None
    user.reset_otp_expires_at = None
    db.commit()
    return {"ok": True}
