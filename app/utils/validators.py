import re
from email.utils import parseaddr
from fastapi import status
from fastapi.responses import JSONResponse

EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")

def is_valid_email(email: str) -> bool:
    return bool(EMAIL_REGEX.fullmatch(email.strip()))

def is_valid_phone(phone: str) -> bool:
    phone = re.sub(r"\D", "", phone)  # Remove non-digits
    return 10 <= len(phone) <= 15


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