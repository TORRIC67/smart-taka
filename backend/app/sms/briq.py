"""Briq (Karibu) SMS provider.

From the Briq docs:  POST https://karibu.briq.tz/v1/message/send-instant
  header  X-API-Key: <your key>
  body    {"content": "...", "recipients": ["255..."], "sender_id": "..."}
Briq fails the WHOLE request if one number is invalid, so we send one recipient per request.
"""
import httpx

from app.core.phone import to_international

from .base import SmsProvider, SmsResult


def _error_text(data: dict, status: int) -> str:
    """Briq reports errors in a few shapes; turn any of them into one short sentence."""
    if isinstance(data.get("errors"), list) and data["errors"]:
        return "; ".join(str(e.get("message", e)) for e in data["errors"])[:300]
    detail = data.get("detail")
    if isinstance(detail, dict):
        detail = detail.get("message") or detail.get("description") or detail
    return str(detail or data.get("message") or f"HTTP {status}")[:300]


class BriqSmsProvider(SmsProvider):
    def __init__(self, api_key: str, sender_id: str, base_url: str = "https://karibu.briq.tz", timeout: float = 20.0):
        self._sender_id = sender_id
        self._client = httpx.Client(base_url=base_url, timeout=timeout, headers={"X-API-Key": api_key})

    def send(self, phone: str, message: str) -> SmsResult:
        try:
            resp = self._client.post(
                "/v1/message/send-instant",
                json={"content": message, "recipients": [to_international(phone)], "sender_id": self._sender_id},
            )
        except (httpx.HTTPError, ValueError) as exc:  # ValueError = bad phone format
            return SmsResult(ok=False, error=f"Briq request failed: {exc}"[:300])

        try:
            data = resp.json()
        except ValueError:
            data = {}
        if resp.status_code < 400 and data.get("success"):
            return SmsResult(ok=True, provider_ref=data.get("job_id"))
        return SmsResult(ok=False, error=_error_text(data, resp.status_code))
