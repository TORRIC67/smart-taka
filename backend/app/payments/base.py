"""Payment abstraction layer.

The rest of Smart Taka only talks to `PaymentProvider`. HarakaPay is just one
implementation, so if you change provider later you write one new class and
nothing else in the system changes.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class PaymentStatus(str, Enum):
    PENDING = "pending"            # USSD push sent, customer has not approved yet
    COMPLETED = "completed"        # money received -> customer counts as paid
    FAILED = "failed"              # customer cancelled / timed out / no funds
    NEEDS_REVIEW = "needs_review"  # provider says completed but the amount does not match; admin must check


class PaymentProviderError(Exception):
    """Raised when the provider rejects a request or cannot be reached."""


@dataclass
class CollectResult:
    order_id: str      # provider's reference - we save it and use it to check status later
    amount: int        # what the customer is charged (TZS)
    fee: int           # provider fee (TZS)
    net_amount: int    # what Smart Taka receives (TZS)


@dataclass
class StatusResult:
    order_id: str
    status: PaymentStatus
    amount: int
    fee: int
    net_amount: int
    completed_at: Optional[str] = None  # ISO timestamp from provider


class PaymentProvider(ABC):
    @abstractmethod
    def collect(
        self,
        phone: str,
        amount: int,
        description: str = "",
        webhook_url: Optional[str] = None,
    ) -> CollectResult:
        """Ask the customer to pay (USSD push). Returns immediately;
        the final result arrives later via webhook or via get_status()."""

    @abstractmethod
    def get_status(self, order_id: str) -> StatusResult:
        """Ask the provider for the current state of one payment."""
