"""SMS abstraction. The rest of the app only knows SmsProvider, never Briq directly."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class SmsResult:
    ok: bool
    provider_ref: Optional[str] = None
    error: Optional[str] = None


class SmsProvider(ABC):
    @abstractmethod
    def send(self, phone: str, message: str) -> SmsResult:
        """Send one SMS. Must NOT raise: return SmsResult(ok=False, error=...) so a bulk send can continue."""
