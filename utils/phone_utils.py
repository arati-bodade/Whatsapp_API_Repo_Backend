import re

def normalize_phone(phone: str | None) -> str | None:
    if not phone:
        return None

    phone = str(phone).strip()

    # If JID format exists, extract number before "@"
    if "@" in phone:
        phone = phone.split("@")[0]

    # Remove all non-digit characters
    phone = re.sub(r"\D", "", phone)

    # Valid WhatsApp numbers or LIDs can be up to 25 digits
    if not phone or len(phone) < 5 or len(phone) > 25:
        return None

    return phone
