"""Payment business logic. Routers call these functions; these call the provider.

Flow with HarakaPay (it is asynchronous, unlike a simple "confirm" call):
  1. start_payment()  -> HarakaPay sends a USSD push to the customer's phone.
                         We save a row with status 'pending' + HarakaPay's order_id.
  2. Customer enters their PIN on the phone.
  3. HarakaPay POSTs to our webhook  (or reconcile_pending() finds it later).
  4. sync_payment()   -> asks HarakaPay for the REAL status, then marks the payment
                         'completed' and runs on_payment_completed() exactly once.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.payment import Payment

from .base import PaymentProvider, PaymentStatus

log = logging.getLogger(__name__)

# If the customer taps "Pay" twice, don't send a second USSD push within this window.
PENDING_REUSE_WINDOW = timedelta(minutes=3)


class AlreadyPaidError(Exception):
    """Customer already has a completed payment for this billing period."""


class PaymentNotFoundError(Exception):
    """No payment row with this order_id (never trust order_ids from outside blindly)."""


def on_payment_completed(db: Session, payment: Payment) -> None:
    """Runs exactly once, inside the same DB transaction, when a payment becomes 'completed'.
    Calls confirm_payment() (app/services/billing.py): marks the customer as paid and adds
    their location to today's collection list."""
    from app.services.billing import confirm_payment

    confirm_payment(db, payment.customer_id, payment.amount)


def _parse_ts(value: Optional[str]) -> datetime:
    """HarakaPay timestamps look like 2026-01-24T12:01:30Z."""
    if value:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            pass
    return datetime.now(timezone.utc)


def start_payment(
    db: Session,
    provider: PaymentProvider,
    *,
    customer_id: int,
    phone: str,
    amount: int,
    billing_period: str,
    webhook_url: Optional[str],
) -> Payment:
    # 1) Already paid this month? Then never charge again.
    already_paid = db.scalar(
        select(Payment).where(
            Payment.customer_id == customer_id,
            Payment.billing_period == billing_period,
            Payment.status == PaymentStatus.COMPLETED.value,
        )
    )
    if already_paid:
        raise AlreadyPaidError(f"Customer {customer_id} already paid for {billing_period}")

    # 2) A very recent pending attempt? Return it instead of sending another USSD push.
    cutoff = datetime.now(timezone.utc) - PENDING_REUSE_WINDOW
    recent = db.scalar(
        select(Payment).where(
            Payment.customer_id == customer_id,
            Payment.billing_period == billing_period,
            Payment.status == PaymentStatus.PENDING.value,
            Payment.created_at > cutoff,
        )
    )
    if recent:
        return recent

    # 3) Ask HarakaPay to push the USSD prompt to the customer's phone.
    result = provider.collect(
        phone=phone,
        amount=amount,
        description=f"Smart Taka {billing_period}",
        webhook_url=webhook_url,
    )

    payment = Payment(
        customer_id=customer_id,
        provider="harakapay",
        order_id=result.order_id,
        phone=phone,
        billing_period=billing_period,
        amount=result.amount,
        fee=result.fee,
        net_amount=result.net_amount,
        status=PaymentStatus.PENDING.value,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


def sync_payment(db: Session, provider: PaymentProvider, order_id: str) -> Payment:
    """Bring one payment up to date with HarakaPay. Safe to call many times (idempotent):
    webhook + polling + reconcile can all hit it and the customer is still only confirmed once.

    IMPORTANT: we never trust the webhook body. The webhook only tells us *which* order to
    check; the real status always comes from HarakaPay's status endpoint.
    """
    try:
        # FOR UPDATE = lock the row so two simultaneous calls can't both confirm it.
        payment = db.scalar(select(Payment).where(Payment.order_id == order_id).with_for_update())
        if payment is None:
            raise PaymentNotFoundError(order_id)

        if payment.status != PaymentStatus.PENDING.value:
            db.commit()  # nothing to do - just release the lock
            return payment

        result = provider.get_status(order_id)

        if result.status == PaymentStatus.COMPLETED:
            if result.amount != payment.amount:
                # Money arrived but the amount is not what we asked for -> let an admin look at it.
                log.error("Amount mismatch on %s: expected %s got %s", order_id, payment.amount, result.amount)
                payment.status = PaymentStatus.NEEDS_REVIEW.value
            else:
                payment.status = PaymentStatus.COMPLETED.value
                payment.fee = result.fee
                payment.net_amount = result.net_amount
                payment.completed_at = _parse_ts(result.completed_at)
                on_payment_completed(db, payment)  # same transaction: all-or-nothing
        elif result.status == PaymentStatus.FAILED:
            payment.status = PaymentStatus.FAILED.value
        # else: still pending, leave it

        db.commit()
        db.refresh(payment)
        return payment
    except Exception:
        db.rollback()
        raise


def reconcile_pending(db: Session, provider: PaymentProvider, min_age_seconds: int = 60) -> int:
    """Safety net: check every payment still 'pending'. Run this every minute or two
    (cron / APScheduler / Celery beat). It covers a lost webhook or a server that was down.
    Returns how many payments changed state."""
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=min_age_seconds)
    order_ids = db.scalars(
        select(Payment.order_id).where(
            Payment.status == PaymentStatus.PENDING.value,
            Payment.created_at < cutoff,
        )
    ).all()

    changed = 0
    for oid in order_ids:
        try:
            if sync_payment(db, provider, oid).status != PaymentStatus.PENDING.value:
                changed += 1
        except Exception:  # one bad payment must not stop the rest
            log.exception("Reconcile failed for %s", oid)
    return changed
