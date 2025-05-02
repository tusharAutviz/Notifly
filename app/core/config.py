from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    PROJECT_NAME: str = "Messaging Platform"
    API_V1_STR: str = "/api/v1"

    # Database
    DATABASE_URL: str = "sqlite:///./dev.db"

    # JWT
    SECRET_KEY: str = "your_custom_secret_key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 3600
    REFRESH_TOKEN_EXPIRE_DAYS: int = 1

    # CORS
    ALLOWED_ORIGINS: List[str] = ["*"]  # Replace in production

    # Email Settings
    EMAIL_FROM: str = "basix0805@gmail.com"
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = "basix0805@gmail.com"
    SMTP_PASSWORD: str = ""
    SMTP_TLS: bool = True

    # Twilio Settings
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""

    # OTP Settings
    OTP_EXPIRY_MINUTES: int = 10

    class Config:
        env_file = ".env"

settings = Settings()
