"""Meseji (meseji.co.tz) SMS provider.

From the Meseji docs:
  POST https://meseji.co.tz/api/v1/sms/send
  header  x-api-key: <your_api_key>
  body    {"sender_id": "...", "message": "...", "contacts": "255712345678"}
  success {"batch_id": "...", "total_recipients": 1, "estimated_cost": 20, "status": "queued"}

The docs don't show an error response shape, so on failure this looks for any of the
common message fields Meseji might use and falls back to the HTTP status code.
"""
import httpx

from app.core.phone import to_international

from .base import SmsProvider, SmsResult


def _error_text(data: dict, status: int) -> str:
    if isinstance(data.get("errors"), list) and data["errors"]:
        return "; ".join(str(e.get("message", e)) for e in data["errors"])[:300]
    return str(data.get("message") or data.get("error") or data.get("detail") or f"HTTP {status}")[:300]


class MesejiSmsProvider(SmsProvider):
    def __init__(
        self, api_key: str, sender_id: str, base_url: str = "https://meseji.co.tz/api/v1", timeout: float = 20.0
    ):
        self._sender_id = sender_id
        self._client = httpx.Client(base_url=base_url, timeout=timeout, headers={"x-api-key": api_key})

    def send(self, phone: str, message: str) -> SmsResult:
        try:
            resp = self._client.post(
                "/sms/send",
                json={"sender_id": self._sender_id, "message": message, "contacts": to_international(phone)},
            )
        except (httpx.HTTPError, ValueError) as exc:  # ValueError = bad phone format
            return SmsResult(ok=False, error=f"Meseji request failed: {exc}"[:300])

        try:
            data = resp.json()
        except ValueError:
            data = {}
        # Success responses carry a batch_id; nothing in the docs signals failure explicitly,
        # so treat "no batch_id" or a 4xx/5xx status as failure.
        if resp.status_code < 400 and data.get("batch_id"):
            return SmsResult(ok=True, provider_ref=data.get("batch_id"))
        return SmsResult(ok=False, error=_error_text(data, resp.status_code))
