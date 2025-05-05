import re
from email.utils import parseaddr
from fastapi import status
from fastapi.responses import JSONResponse

EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")

def is_valid_email(email: str) -> bool:
    return bool(EMAIL_REGEX.fullmatch(email.strip()))

def is_valid_phone(phone: str) -> tuple[bool, str]:
    phone = phone.strip()
    
    # Remove all non-digit characters except a leading '+'
    if phone.startswith('+'):
        digits_only = '+' + re.sub(r'\D', '', phone[1:])
    else:
        digits_only = '+' + re.sub(r'\D', '', phone)

    # Validate length after cleaning
    if 11 <= len(digits_only) <= 16:  # + followed by 10-15 digits
        return True, digits_only
    else:
        return False, digits_only


def create_response(status_code, message=None, data=None, detail=None):
    content = {
        "status": status_code,
        "message": message,
    }
    
    if data is not None:
        content["data"] = data

    if detail is not None:
        content["detail"] = detail

    return JSONResponse(content=content, status_code=status_code)