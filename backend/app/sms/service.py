"""Billing SMS logic: build the message, send it, log it, and move the customer to 'billed'."""
from functools import lru_cache
from typing import List

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.customer import Customer, PaymentStatus
from app.models.payment import Payment
from app.models.sms_log import SmsLog

from .base import SmsProvider
from .briq import BriqSmsProvider
from .meseji import MesejiSmsProvider
from .mock import MockSmsProvider


@lru_cache
def get_sms_provider() -> SmsProvider:
    if settings.SMS_PROVIDER == "briq":
        if not settings.BRIQ_API_KEY or not settings.BRIQ_SENDER_ID:
            raise RuntimeError("SMS_PROVIDER=briq needs BRIQ_API_KEY and BRIQ_SENDER_ID in .env")
        return BriqSmsProvider(settings.BRIQ_API_KEY, settings.BRIQ_SENDER_ID, settings.BRIQ_BASE_URL)
    if settings.SMS_PROVIDER == "meseji":
        if not settings.MESEJI_API_KEY:
            raise RuntimeError("SMS_PROVIDER=meseji needs MESEJI_API_KEY in .env")
        return MesejiSmsProvider(settings.MESEJI_API_KEY, settings.MESEJI_SENDER_ID, settings.MESEJI_BASE_URL)
    return MockSmsProvider()


def billing_message(full_name: str, period: str) -> str:
    """The text customers receive. Edit the wording here. Keep it short: every 160 characters = 1 SMS charged."""
    first_name = full_name.split()[0]
    return (
        f"Smart Taka: Habari {first_name}, ada ya taka ya {period} ni TZS {settings.MONTHLY_FEE_TZS:,}. "
        f"Lipia kwa kuingia {settings.APP_URL}, bonyeza Make payment na uweke PIN ya simu. Asante."
    )


def send_billing_sms(db: Session, provider: SmsProvider, customers: List[Customer], period: str, force: bool = False) -> dict:
    """Send the billing SMS to each customer who has not paid for `period`.
    - Already paid this period      -> skipped
    - Already got the SMS this period -> skipped (so a double click never costs you twice), unless force=True
    - A customer marked 'paid' from an OLDER month is moved back to unpaid here: this is the monthly reset."""
    out = {"sent": 0, "failed": 0, "already_sent": 0, "skipped_paid": 0, "details": []}

    paid_ids = set(
        db.scalars(select(Payment.customer_id).where(Payment.billing_period == period, Payment.status == "completed"))
    )
    sent_ids = set(
        db.scalars(select(SmsLog.customer_id).where(SmsLog.period == period, SmsLog.kind == "billing", SmsLog.status == "ok"))
    )

    for c in customers:
        if c.id in paid_ids:
            c.payment_status = PaymentStatus.PAID
            out["skipped_paid"] += 1
            continue
        if c.payment_status == PaymentStatus.PAID:  # paid in an older month: new month starts now
            c.payment_status = PaymentStatus.REGISTERED
        if c.id in sent_ids and not force:
            c.payment_status = PaymentStatus.BILLED
            out["already_sent"] += 1
            continue

        message = billing_message(c.full_name, period)
        result = provider.send(c.phone, message)
        db.add(
            SmsLog(
                customer_id=c.id,
                period=period,
                phone=c.phone,
                message=message,
                status="ok" if result.ok else "failed",
                error=result.error,
                provider_ref=result.provider_ref,
            )
        )
        if result.ok:
            c.payment_status = PaymentStatus.BILLED
            out["sent"] += 1
        else:
            out["failed"] += 1
        out["details"].append({"customer_id": c.id, "name": c.full_name, "ok": result.ok, "error": result.error})

    db.commit()
    return out
