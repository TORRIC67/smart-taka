"""FAKE payment provider for development ONLY.

Use it while your HarakaPay account is not verified, so you can test the whole flow
(collect -> pending -> completed -> customer paid -> added to today's list) without real money.

Turn it on in .env:   PAYMENT_PROVIDER=mock
NEVER use it in production: it "confirms" every payment automatically, so anyone could get service for free.

It keeps no state: the order_id itself carries the time and amount ("MOCK-<ms>-<amount>"),
so it keeps working even when uvicorn --reload restarts the server.
"""
import time
from typing import Optional

from .base import CollectResult, PaymentProvider, PaymentProviderError, PaymentStatus, StatusResult

COMPLETE_AFTER_SECONDS = 8  # pretend the customer needs 8 seconds to enter their PIN
FEE_RATE = 0.06            # pretend fee, similar to the HarakaPay example


class MockProvider(PaymentProvider):
    def collect(
        self,
        phone: str,
        amount: int,
        description: str = "",
        webhook_url: Optional[str] = None,
    ) -> CollectResult:
        fee = round(amount * FEE_RATE)
        order_id = f"MOCK-{int(time.time() * 1000)}-{amount}"
        return CollectResult(order_id=order_id, amount=amount, fee=fee, net_amount=amount - fee)

    def get_status(self, order_id: str) -> StatusResult:
        try:
            _, ts_ms, amount = order_id.split("-")
            started, amount = int(ts_ms) / 1000, int(amount)
        except ValueError:
            raise PaymentProviderError(f"Unknown mock order: {order_id}")

        fee = round(amount * FEE_RATE)
        done = time.time() - started >= COMPLETE_AFTER_SECONDS
        return StatusResult(
            order_id=order_id,
            status=PaymentStatus.COMPLETED if done else PaymentStatus.PENDING,
            amount=amount,
            fee=fee,
            net_amount=amount - fee,
            completed_at=None,  # service falls back to "now"
        )

    def get_balance(self) -> dict:
        return {"wallet_balance": 0, "float_balance": 0}
