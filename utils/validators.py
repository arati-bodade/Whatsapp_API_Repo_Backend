import re
from typing import Optional


def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_phone(phone: str) -> bool:
    """Validate phone number format."""
    # Remove any non-digit characters
    digits_only = re.sub(r'\D', '', phone)
    return len(digits_only) >= 10 and len(digits_only) <= 15


def validate_gstin(gstin: Optional[str]) -> bool:
    """Validate GSTIN format (Indian GST identification)."""
    if not gstin:
        return True  # GSTIN is optional
    pattern = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[0-9]{1}[A-Z]{1}[0-9]{1}$'
    return re.match(pattern, gstin) is not None
