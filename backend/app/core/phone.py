"""One place that decides how phone numbers are stored: local format 0712345678."""
import re


def normalize_phone(raw: str) -> str:
    """Accepts +255712345678, 255712345678, 0712 345 678 ... and returns 0712345678."""
    p = re.sub(r"[\s\-+]", "", raw or "")
    if p.startswith("255") and len(p) == 12:
        p = "0" + p[3:]
    if not re.fullmatch(r"0\d{9}", p):
        raise ValueError(f"Invalid phone number: {raw!r}")
    return p


def to_international(raw: str) -> str:
    """0714617609 -> 255714617609 (the format Briq expects)."""
    return "255" + normalize_phone(raw)[1:]


def to_international(local: str) -> str:
    """0714617609 -> 255714617609 (the format SMS providers like best)."""
    return "255" + normalize_phone(local)[1:]
