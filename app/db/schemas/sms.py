from pydantic import BaseModel

class SMSRequest(BaseModel):
    phone_number: str
    recipient_name: str
    message: str
