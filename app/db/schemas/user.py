from pydantic import BaseModel
from typing import Optional

class CreateUser(BaseModel):
    name: str
    email: str
    mobile_no: str
    password: str
    school_id: int

class LoginUser(BaseModel):
    username: str
    password: str

class VerifyOTP(BaseModel):
    email: str
    otp: str


class ResendOtp(BaseModel):
    email: str

class RegenerateAccessToken(BaseModel):
    refresh_token: str

class ForgotPassword(BaseModel):
    email: str

class NewPassword(BaseModel):
    email: str
    password: str
    reset_token: str

class ResetPassword(BaseModel):
    password: str
    new_password: str

class UpdateUser(BaseModel):
    user_id: int
    is_active: bool
