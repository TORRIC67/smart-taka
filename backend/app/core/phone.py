"""One place that decides how phone numbers are stored and validated.

Two layers on purpose:

* normalize_phone()  - lenient. Only fixes the FORMAT (+255..., 255..., spaces -> 0712345678).
  Used wherever a number that is ALREADY stored is looked up or used (login, OTP, SMS,
  mobile-money push). It must never reject an existing account's number.

* validate_tz_mobile() - strict. Used ONLY when a number is typed in as NEW data
  (registering a customer/driver/agent/admin, editing a phone, paying from another phone).
  It makes sure the number is a real-looking Tanzanian mobile number, not just any 10 digits.
"""
import re

# Mobile prefixes in the TCRA National Numbering Plan (the 3 digits after the leading 0).
# If TCRA assigns a new range, add it here - this is the only place that needs to change.
TZ_MOBILE_PREFIXES = {
    "061", "062",                 # Halotel
    "065", "066", "067", "071", "077",  # Yas (Tigo / Zantel), Smile
    "068", "069", "078",          # Airtel
    "073",                        # TTCL
    "074", "075", "076", "079",   # Vodacom
}

_INVALID_MSG = (
    "Namba ya simu si sahihi. Tumia namba ya simu ya Tanzania, mfano 0754 123 456 au +255 754 123 456. "
    "/ Invalid phone number. Use a Tanzanian mobile number, e.g. 0754 123 456 or +255 754 123 456."
)


def normalize_phone(raw: str) -> str:
    """Accepts +255712345678, 255712345678, 0712 345 678 ... and returns 0712345678."""
    p = re.sub(r"[\s\-+]", "", raw or "")
    if p.startswith("255") and len(p) == 12:
        p = "0" + p[3:]
    if not re.fullmatch(r"0\d{9}", p):
        raise ValueError(f"Invalid phone number: {raw!r}")
    return p


def _looks_made_up(subscriber: str) -> bool:
    """The 7 digits after the 3-digit prefix: all the same (0711111111) or a straight run
    (1234567 / 7654321) are what people type when they just want to get past the form."""
    if len(set(subscriber)) == 1:
        return True
    digits = [int(c) for c in subscriber]
    steps = {digits[i + 1] - digits[i] for i in range(len(digits) - 1)}
    return steps == {1} or steps == {-1}


def validate_tz_mobile(raw: str) -> str:
    """Strict check for NEW numbers. Returns the number in the stored form (0754123456)
    or raises ValueError with a message that is safe to show the user."""
    try:
        local = normalize_phone(raw)
    except ValueError:
        raise ValueError(_INVALID_MSG)
    if local[:3] not in TZ_MOBILE_PREFIXES:
        raise ValueError(_INVALID_MSG)
    if _looks_made_up(local[3:]):
        raise ValueError(_INVALID_MSG)
    return local


def to_international(local: str) -> str:
    """0714617609 -> 255714617609 (the format SMS providers like best)."""
    return "255" + normalize_phone(local)[1:]
