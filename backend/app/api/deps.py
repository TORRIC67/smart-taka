"""Shared dependencies: database session, current user, role check."""
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import SessionLocal
from app.models.user import User

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
