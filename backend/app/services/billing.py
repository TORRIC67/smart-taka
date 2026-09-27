"""Business rules that run when money arrives.

confirm_payment() is the function your original design called "confirm_payment(customer_id, amount)".
The payment module calls it exactly once per successful payment (see payments/service.py).
It must NOT commit - the caller commits, so the payment and the customer update succeed together.
"""
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.customer import Customer, PaymentStatus
from app.models.route import CollectionStop

TZ = ZoneInfo("Africa/Dar_es_Salaam")  # "today" must mean today in Tanzania, not on the server


def today_tz():
    return datetime.now(TZ).date()


def confirm_payment(db: Session, customer_id: int, amount: int) -> None:
    customer = db.get(Customer, customer_id)
    customer.payment_status = PaymentStatus.PAID

    # Add the customer's location to today's collection list (once only).
    today = today_tz()
    already = db.scalar(
        select(CollectionStop).where(CollectionStop.customer_id == customer_id, CollectionStop.stop_date == today)
    )
    if already is None:
        db.add(CollectionStop(stop_date=today, customer_id=customer_id))
    db.flush()
