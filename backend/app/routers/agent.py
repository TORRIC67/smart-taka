"""Field agent (door-to-door collector) endpoints.

An agent can only ever see and register customers in the street(s)/mitaa an admin has
assigned them - never edit or remove anyone, and never touch any other part of the system.
If something needs to change, they contact their admin."""
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models.agent_ward import AgentWard
from app.models.customer import Customer
from app.models.user import Role, User
from app.schemas import CustomerCreate, CustomerOut
from app.services.customers import create_customer

router = APIRouter(prefix="/agent", tags=["agent"], dependencies=[Depends(require_roles(Role.AGENT))])


def _my_wards(db: Session, user: User) -> List[str]:
    return list(db.scalars(select(AgentWard.ward).where(AgentWard.user_id == user.id).order_by(AgentWard.ward)).all())


@router.get("/my-wards")
def my_wards(user: User = Depends(require_roles(Role.AGENT)), db: Session = Depends(get_db)):
    return {"wards": _my_wards(db, user)}


@router.get("/customers", response_model=List[CustomerOut])
def list_my_customers(user: User = Depends(require_roles(Role.AGENT)), db: Session = Depends(get_db)):
    wards = _my_wards(db, user)
    if not wards:
        return []
    return db.scalars(
        select(Customer).where(Customer.provider_id == user.provider_id, Customer.ward.in_(wards)).order_by(Customer.id)
    ).all()


@router.post("/customers", response_model=CustomerOut, status_code=201)
def register_my_customer(data: CustomerCreate, user: User = Depends(require_roles(Role.AGENT)), db: Session = Depends(get_db)):
    wards = _my_wards(db, user)
    if data.ward not in wards:
        raise HTTPException(400, "You can only register customers in a street assigned to you")
    return create_customer(db, data, provider_id=user.provider_id)
