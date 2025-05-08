import random
import string
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.db.models.user import User
import secrets


def generate_reset_token():
    return secrets.token_urlsafe(32)  # e.g., 'RANDOM-TOKEN-STRING'

def generate_otp(length: int = 4) -> str:
    """Generate a random OTP of specified length"""
    return ''.join(random.choices(string.digits, k=length))

def save_otp_to_user(db : Session, email: str, otp: str) -> bool:
    """Save OTP to user record"""
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return False

        user.otp = otp
        user.otp_created_at = datetime.now(timezone.utc)
        db.commit()
        return True
    except Exception:
        db.rollback()
        return False

def verify_otp(db: Session, email: str, otp: str, expiry_minutes: int = 10) -> bool:
    """Verify OTP for a user"""
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user or not user.otp or not user.otp_created_at:
            return False

        # Check if OTP matches
        if user.otp != otp:
            return False

        # Check if OTP is expired
        expiry_time = user.otp_created_at + timedelta(minutes=expiry_minutes)
        expiry_time_timezone = expiry_time.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > expiry_time_timezone:
            return False

        if user.otp_verified:
            reset_token = generate_reset_token()
            user.otp = reset_token
            user.otp_created_at = datetime.now(timezone.utc)
            db.commit()
            return reset_token
    
        # Mark user as verified
        user.otp_verified = True
        user.otp = None  # Clear OTP after successful verification
        db.commit()
        return True
    except Exception:
        db.rollback()
        return False
