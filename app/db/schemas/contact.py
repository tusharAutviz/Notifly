from pydantic import BaseModel

class Contacts(BaseModel):
    student_name: str
    parent_name: str
    parent_email: str
    parent_phone_no: str
    mode: str