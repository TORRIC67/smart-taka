"""Customers send complaints/ratings; admin reads them."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_optional_scope, require_roles
from app.models.complaint import Complaint
from app.models.customer import Customer
from app.models.user import Role, User
from app.schemas import ComplaintCreate

router = APIRouter(prefix="/complaints", tags=["complaints"])


@router.post("", status_code=201)
def submit_complaint(
    data: ComplaintCreate,
    user: User = Depends(require_roles(Role.RESIDENT)),
    db: Session = Depends(get_db),
):
    customer = db.scalar(select(Customer).where(Customer.user_id == user.id))
    if customer is None:
        raise HTTPException(404, "No customer profile for this user")
    complaint = Complaint(customer_id=customer.id, rating=data.rating, message=data.message)
    db.add(complaint)
    db.commit()
    return {"id": complaint.id}


@router.get("", dependencies=[Depends(require_roles(*Role.ADMINS))])
def list_complaints(scope: Optional[int] = Depends(get_optional_scope), db: Session = Depends(get_db)) -> List[dict]:
    q = select(Complaint, Customer).join(Customer, Customer.id == Complaint.customer_id)
    if scope is not None:
        q = q.where(Customer.provider_id == scope)
    rows = db.execute(q.order_by(Complaint.created_at.desc())).all()
    return [
        {
            "id": c.id,
            "customer_id": cu.id,
            "customer_name": cu.full_name,
            "ward": cu.ward,
            "rating": c.rating,
            "message": c.message,
            "created_at": c.created_at,
        }
        for c, cu in rows
    ]
