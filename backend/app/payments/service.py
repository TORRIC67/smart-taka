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
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.payment import Payment

from .base import PaymentProvider, PaymentProviderError, PaymentStatus

log = logging.getLogger(__name__)


class AlreadyPaidError(Exception):
    """Customer already has a completed payment for this billing period."""


class PaymentNotFoundError(Exception):
    """No payment row with this order_id (never trust order_ids from outside blindly)."""


class InsufficientWalletError(Exception):
    """Wallet balance is too low to cover this bill."""


def on_payment_completed(db: Session, payment: Payment) -> None:
    """Runs exactly once, inside the same DB transaction, when a payment becomes 'completed'.
    A normal monthly-bill payment marks the customer paid and adds them to today's collection
    list (see app/services/billing.py). A wallet top-up instead just credits their balance -
    it isn't for any particular month, so it doesn't touch payment_status or the route."""
    if payment.purpose == "wallet_topup":
        customer = db.get(Customer, payment.customer_id)
        customer.wallet_balance_tzs += payment.amount
        db.flush()
    else:
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
    provider_id: Optional[int] = None,  # the customer's ZONE (ServiceProvider), not the payment gateway
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

    # 2) Idempotency check: is there ALREADY a pending attempt for this customer+period?
    # Don't trust our own stale 'pending' row - ask the provider RIGHT NOW what really
    # happened to it. This is what stops a customer from being charged twice: if HarakaPay
    # already approved it but our webhook hasn't arrived yet, we catch that here instead of
    # sending a second USSD push.
    pending = db.scalar(
        select(Payment)
        .where(Payment.customer_id == customer_id, Payment.billing_period == billing_period, Payment.status == PaymentStatus.PENDING.value)
        .order_by(Payment.created_at.desc())
    )
    if pending is not None:
        fresh = sync_payment(db, provider, pending.order_id)  # re-checks with the provider, not our DB
        if fresh.status == PaymentStatus.COMPLETED.value:
            raise AlreadyPaidError(f"Customer {customer_id} already paid for {billing_period}")
        if fresh.status == PaymentStatus.PENDING.value:
            return fresh  # still waiting on that same push - never start a second one
        # FAILED or NEEDS_REVIEW: that attempt is done, fall through and start a fresh one

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
        provider_id=provider_id,
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


# ---------------------------------------------------------------- wallet
def start_wallet_topup(
    db: Session,
    provider: PaymentProvider,
    *,
    customer_id: int,
    phone: str,
    amount: int,
    webhook_url: Optional[str],
    provider_id: Optional[int] = None,
) -> Payment:
    """Customer adds money to their own wallet balance (not tied to any billing period).
    Same idempotency protection as start_payment: reuse/verify a pending top-up instead of
    pushing a second USSD prompt."""
    pending = db.scalar(
        select(Payment)
        .where(Payment.customer_id == customer_id, Payment.purpose == "wallet_topup", Payment.status == PaymentStatus.PENDING.value)
        .order_by(Payment.created_at.desc())
    )
    if pending is not None:
        fresh = sync_payment(db, provider, pending.order_id)
        if fresh.status == PaymentStatus.PENDING.value:
            return fresh

    result = provider.collect(phone=phone, amount=amount, description="Smart Taka - wallet top-up", webhook_url=webhook_url)
    payment = Payment(
        customer_id=customer_id, provider="harakapay", order_id=result.order_id, phone=phone,
        billing_period="WALLET", amount=result.amount, fee=result.fee, net_amount=result.net_amount,
        status=PaymentStatus.PENDING.value, provider_id=provider_id, purpose="wallet_topup",
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


def pay_bill_from_wallet(db: Session, *, customer: Customer, billing_period: str, fee_amount: int) -> Payment:
    """Pays this month's bill instantly out of the customer's wallet balance - no mobile-money
    gateway call needed, so it completes immediately instead of waiting for USSD approval."""
    already_paid = db.scalar(
        select(Payment).where(
            Payment.customer_id == customer.id, Payment.billing_period == billing_period,
            Payment.status == PaymentStatus.COMPLETED.value,
        )
    )
    if already_paid:
        raise AlreadyPaidError(f"Customer {customer.id} already paid for {billing_period}")
    if customer.wallet_balance_tzs < fee_amount:
        raise InsufficientWalletError("Wallet balance is too low")

    customer.wallet_balance_tzs -= fee_amount
    payment = Payment(
        customer_id=customer.id, provider="wallet",
        order_id=f"WALLET-{customer.id}-{billing_period}-{int(datetime.now(timezone.utc).timestamp())}",
        phone=customer.phone, billing_period=billing_period, amount=fee_amount, fee=0, net_amount=fee_amount,
        status=PaymentStatus.COMPLETED.value, completed_at=datetime.now(timezone.utc),
        provider_id=customer.provider_id, purpose="monthly_bill",
    )
    db.add(payment)
    db.flush()
    on_payment_completed(db, payment)
    db.commit()
    db.refresh(payment)
    return payment
