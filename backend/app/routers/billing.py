"""Admin: send the monthly billing SMS, and see the SMS history."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_optional_scope, require_roles
from app.core.config import settings
from app.models.customer import Customer
from app.models.sms_log import SmsLog
from app.models.user import Role, User
from app.services.billing import today_tz
from app.sms.service import get_sms_provider, send_billing_sms

router = APIRouter(prefix="/admin", tags=["billing"], dependencies=[Depends(require_roles(*Role.ADMINS))])


class BillingRequest(BaseModel):
    customer_ids: Optional[List[int]] = None  # leave empty = every customer (in your zone)
    billing_period: Optional[str] = Field(default=None, pattern=r"^\d{4}-\d{2}$")  # default: this month
    force: bool = False  # True = send again even if this month's SMS already went out


@router.post("/billing/send")
def send_billing(body: BillingRequest, scope: Optional[int] = Depends(get_optional_scope), db: Session = Depends(get_db)):
    try:
        provider = get_sms_provider()
    except RuntimeError as exc:
        raise HTTPException(503, str(exc))

    period = body.billing_period or today_tz().strftime("%Y-%m")
    query = select(Customer).join(User, User.id == Customer.user_id).where(User.is_active.is_(True)).order_by(Customer.id)
    if scope is not None:
        query = query.where(Customer.provider_id == scope)
    if body.customer_ids:
        query = query.where(Customer.id.in_(body.customer_ids))
    customers = db.scalars(query).all()
    if not customers:
        raise HTTPException(404, "No customers found")

    result = send_billing_sms(db, provider, customers, period, body.force)
    result.update(billing_period=period, sms_provider=settings.SMS_PROVIDER)
    return result


@router.get("/sms-logs")
def sms_logs(limit: int = 50, scope: Optional[int] = Depends(get_optional_scope), db: Session = Depends(get_db)):
    q = select(SmsLog).order_by(SmsLog.id.desc())
    if scope is not None:
        q = q.join(Customer, Customer.id == SmsLog.customer_id).where(Customer.provider_id == scope)
    rows = db.scalars(q.limit(min(limit, 200))).all()
    return [
        {"id": r.id, "customer_id": r.customer_id, "phone": r.phone, "period": r.period,
         "status": r.status, "error": r.error, "message": r.message, "created_at": r.created_at}
        for r in rows
    ]
