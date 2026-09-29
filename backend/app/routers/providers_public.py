"""Public info needed before someone has logged in - just the list of zones,
so the self-registration form can ask "which zone do you live in".
"""
from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.provider import ServiceProvider

router = APIRouter(prefix="/providers", tags=["providers"])


class ProviderPublicOut(BaseModel):
    id: int
    name: str


@router.get("", response_model=List[ProviderPublicOut])
def list_public_providers(db: Session = Depends(get_db)):
    return db.scalars(select(ServiceProvider).where(ServiceProvider.is_active.is_(True)).order_by(ServiceProvider.name)).all()
