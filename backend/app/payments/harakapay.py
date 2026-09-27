"""HarakaPay implementation of PaymentProvider.

Endpoints used (from HarakaPay docs, auth = X-API-Key header):
  POST /api/v1/collect          -> send USSD push to customer's phone
  GET  /api/v1/status/{order}   -> check one payment
  GET  /api/v1/balance          -> wallet / float balance (admin use)
"""
from typing import Optional
from urllib.parse import quote

import httpx

from app.core.phone import normalize_phone as _normalize_phone

from .base import (
    CollectResult,
    PaymentProvider,
    PaymentProviderError,
    PaymentStatus,
    StatusResult,
)

# HarakaPay only reports "completed" or "failed" as final states.
# Anything else (e.g. "pending") is treated as still waiting.
_STATUS_MAP = {
    "completed": PaymentStatus.COMPLETED,
    "failed": PaymentStatus.FAILED,
}


# Docs say TZS 100, but the live API rejected 100 and asked for at least TZS 200. Trust the live API.
MIN_AMOUNT_TZS = 200


def normalize_phone(raw: str) -> str:
    """HarakaPay expects local format like 0712345678 (shared rule lives in app/core/phone.py)."""
    try:
        return _normalize_phone(raw)
    except ValueError as exc:
        raise PaymentProviderError(str(exc)) from exc


class HarakaPayProvider(PaymentProvider):
    def __init__(self, api_key: str, base_url: str = "https://harakapay.net", timeout: float = 20.0):
        # One shared client = connection reuse. The API key never leaves the backend.
        self._client = httpx.Client(
            base_url=base_url,
            timeout=timeout,
            headers={"X-API-Key": api_key},
        )

    # ---- internal helper: one place that handles every kind of failure ----
    def _request(self, method: str, path: str, **kwargs) -> dict:
        try:
            resp = self._client.request(method, path, **kwargs)
        except httpx.HTTPError as exc:
            raise PaymentProviderError(f"HarakaPay unreachable: {exc}") from exc

        try:
            data = resp.json()
        except ValueError:
            raise PaymentProviderError(f"HarakaPay returned non-JSON (HTTP {resp.status_code})")

        # Docs: failures come back as {"success": false, "error": "..."}
        if resp.status_code >= 400 or not data.get("success"):
            raise PaymentProviderError(data.get("error") or data.get("message") or f"HTTP {resp.status_code}")
        return data

    # ---- PaymentProvider interface ----
    def collect(
        self,
        phone: str,
        amount: int,
        description: str = "",
        webhook_url: Optional[str] = None,
    ) -> CollectResult:
        if amount < MIN_AMOUNT_TZS:
            raise PaymentProviderError(f"Amount is below the HarakaPay minimum (TZS {MIN_AMOUNT_TZS})")

        payload = {"phone": normalize_phone(phone), "amount": amount, "description": description}
        if webhook_url:
            payload["webhook_url"] = webhook_url  # HarakaPay POSTs the final result here

        data = self._request("POST", "/api/v1/collect", json=payload)
        return CollectResult(
            order_id=data["order_id"],
            amount=data.get("amount", amount),
            fee=data.get("fee", 0),
            net_amount=data.get("net_amount", amount),
        )

    def get_status(self, order_id: str) -> StatusResult:
        data = self._request("GET", f"/api/v1/status/{quote(order_id, safe='')}")
        p = data["payment"]
        return StatusResult(
            order_id=p["order_id"],
            status=_STATUS_MAP.get(p.get("status"), PaymentStatus.PENDING),
            amount=p.get("amount", 0),
            # NOTE: /collect calls it "fee" but /status calls it "fee_amount"
            fee=p.get("fee_amount", p.get("fee", 0)),
            net_amount=p.get("net_amount", 0),
            completed_at=p.get("completed_at"),
        )

    # ---- HarakaPay-only extra (not part of the generic interface) ----
    def get_balance(self) -> dict:
        data = self._request("GET", "/api/v1/balance")
        return {"wallet_balance": data["wallet_balance"], "float_balance": data["float_balance"]}
