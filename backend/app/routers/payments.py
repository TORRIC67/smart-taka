"""Payment endpoints.

  POST /payments/collect                 resident (self) or admin -> sends USSD push
  POST /payments/webhooks/harakapay      called by HarakaPay only (secret token in URL)
  GET  /payments/balance                 admin only -> HarakaPay wallet/float
  POST /payments/reconcile               admin only -> re-check all pending payments
  GET  /payments/{order_id}              resident (own) or admin -> current status
"""
import hmac
import logging
from datetime import datetime
from functools import lru_cache
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

# Adjust these imports to match your project:
from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.models.customer import Customer
from app.models.payment import Payment
from app.payments.base import PaymentProvider, PaymentProviderError
from app.payments.harakapay import HarakaPayProvider
from app.payments.mock import MockProvider
from app.payments.service import (
    AlreadyPaidError,
    PaymentNotFoundError,
    reconcile_pending,
    start_payment,
    sync_payment,
)

log = logging.getLogger(__name__)
router = APIRouter(prefix="/payments", tags=["payments"])


@lru_cache
def get_provider() -> PaymentProvider:
    # Cached so we reuse one HTTP client. PAYMENT_PROVIDER=mock swaps in the fake provider (dev only).
    if settings.PAYMENT_PROVIDER == "mock":
        return MockProvider()
    return HarakaPayProvider(settings.HARAKAPAY_API_KEY, settings.HARAKAPAY_BASE_URL)


class CollectRequest(BaseModel):
    customer_id: int
    # "YYYY-MM"; defaults to the current month. Amount is NOT accepted from the client.
    billing_period: Optional[str] = Field(default=None, pattern=r"^\d{4}-\d{2}$")


class PaymentOut(BaseModel):
    order_id: str
    status: str
    amount: int
    billing_period: str
    customer_id: int

    class Config:
        from_attributes = True


def _can_access(user, customer: Customer) -> bool:
    """Admin: everyone. Resident: only their own record. Driver: none."""
    if user.role == "admin":
        return True
    return user.role == "resident" and customer.user_id == user.id


@router.post("/collect", response_model=PaymentOut)
def collect(
    body: CollectRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
    provider: PaymentProvider = Depends(get_provider),
):
    customer = db.get(Customer, body.customer_id)
    if customer is None:
        raise HTTPException(404, "Customer not found")
    if not _can_access(user, customer):
        raise HTTPException(403, "Not allowed")

    period = body.billing_period or datetime.now().strftime("%Y-%m")
    try:
        return start_payment(
            db,
            provider,
            customer_id=customer.id,
            phone=customer.phone,
            amount=settings.MONTHLY_FEE_TZS,  # fixed server-side so nobody can pay less
            billing_period=period,
            webhook_url=settings.HARAKAPAY_WEBHOOK_URL,
        )
    except AlreadyPaidError:
        raise HTTPException(409, "Already paid for this period")
    except PaymentProviderError as exc:
        log.warning("HarakaPay collect failed: %s", exc)
        raise HTTPException(502, f"Payment provider error: {exc}")


@router.post("/webhooks/harakapay")
def harakapay_webhook(
    payload: dict = Body(...),
    token: str = Query(default=""),
    db: Session = Depends(get_db),
    provider: PaymentProvider = Depends(get_provider),
):
    # HarakaPay docs mention no signature, so the URL carries a secret token instead.
    if not hmac.compare_digest(token, settings.HARAKAPAY_WEBHOOK_TOKEN):
        raise HTTPException(403, "Forbidden")

    order_id = payload.get("order_id")
    if order_id:
        try:
            # The body is only a hint. sync_payment re-checks the real status with HarakaPay.
            sync_payment(db, provider, str(order_id))
        except PaymentNotFoundError:
            log.warning("Webhook for unknown order_id %s", order_id)
        except Exception:
            # Still answer 200 (HarakaPay only wants a 200); reconcile_pending will retry it.
            log.exception("Webhook processing failed for %s", order_id)
    return {"ok": True}


@router.get("/balance")
def balance(user=Depends(get_current_user), provider: HarakaPayProvider = Depends(get_provider)):
    if user.role != "admin":
        raise HTTPException(403, "Admin only")
    try:
        return provider.get_balance()
    except PaymentProviderError as exc:
        raise HTTPException(502, str(exc))


@router.post("/reconcile")
def reconcile(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
    provider: PaymentProvider = Depends(get_provider),
):
    if user.role != "admin":
        raise HTTPException(403, "Admin only")
    return {"updated": reconcile_pending(db, provider)}


@router.get("/{order_id}", response_model=PaymentOut)
def payment_status(
    order_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
    provider: PaymentProvider = Depends(get_provider),
):
    """Frontend polls this every few seconds while the customer approves on their phone."""
    payment = db.query(Payment).filter(Payment.order_id == order_id).first()
    if payment is None:
        raise HTTPException(404, "Payment not found")
    customer = db.get(Customer, payment.customer_id)
    if not _can_access(user, customer):
        raise HTTPException(403, "Not allowed")

    try:
        return sync_payment(db, provider, order_id)  # no-op if already final
    except PaymentProviderError:
        return payment  # provider hiccup: just show what we have
