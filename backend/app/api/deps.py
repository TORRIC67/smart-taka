"""Shared dependencies: database session, current user, role check, provider (zone) scope."""
from typing import Optional

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import SessionLocal
from app.models.provider import ServiceProvider
from app.models.user import Role, User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_db():
    with SessionLocal() as db:
        yield db


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    try:
        data = decode_token(token)
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid or expired token")
    user = db.get(User, int(data["sub"]))
    if user is None or not user.is_active:
        raise HTTPException(401, "User not found or disabled")
    return user


def require_roles(*roles: str):
    """Use as Depends(require_roles("admin")) to lock an endpoint to some roles."""

    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(403, "Not allowed for your role")
        return user

    return checker


# ---------------------------------------------------------------- zone (Service Provider) scope
def get_optional_scope(provider_id: Optional[int] = None, user: User = Depends(get_current_user)) -> Optional[int]:
    """For VIEWING things (lists, summaries, reports). None means 'no filter':
    a super admin sees every zone unless they narrow it down with ?provider_id=.
    A regular admin always gets their own zone, no matter what is passed in the URL."""
    if user.role == Role.SUPER_ADMIN:
        return provider_id
    return user.provider_id


def get_required_provider(
    provider_id: Optional[int] = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> ServiceProvider:
    """For ACTIONS that must happen in exactly one zone (generating routes, sending billing SMS).
    A regular admin always acts in their own zone. A super admin must say which one with
    ?provider_id=, since they don't operate trucks themselves."""
    if user.role == Role.SUPER_ADMIN:
        if provider_id is None:
            raise HTTPException(400, "provider_id is required for a super admin")
        provider = db.get(ServiceProvider, provider_id)
        if provider is None:
            raise HTTPException(404, "Service provider not found")
        return provider
    provider = db.get(ServiceProvider, user.provider_id) if user.provider_id else None
    if provider is None:
        raise HTTPException(400, "Your admin account has no service provider assigned")
    return provider
