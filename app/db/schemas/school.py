from pydantic import BaseModel
from typing import Optional


class CreateSchool(BaseModel):
    school_name: str
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    pincode: Optional[str] = None
    phone_no: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    is_active: Optional[bool] = True


class PartialSchoolUpdate(BaseModel):
    school_name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    pincode: Optional[str] = None
    phone_no: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    is_active: Optional[bool] = None