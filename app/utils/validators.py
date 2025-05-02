import re
from email.utils import parseaddr

EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")

def is_valid_email(email: str) -> bool:
    return bool(EMAIL_REGEX.fullmatch(email.strip()))

def is_valid_phone(phone: str) -> bool:
    phone = re.sub(r"\D", "", phone)  # Remove non-digits
    return 10 <= len(phone) <= 15