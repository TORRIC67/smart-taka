"""Fake SMS provider: prints the message in the terminal instead of sending it. Free, safe for testing."""
from .base import SmsProvider, SmsResult


class MockSmsProvider(SmsProvider):
    def send(self, phone: str, message: str) -> SmsResult:
        print(f"\n[MOCK SMS] to {phone}\n{message}\n", flush=True)
        return SmsResult(ok=True, provider_ref="mock")
