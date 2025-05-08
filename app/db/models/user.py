from app.db.base import Base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.base_mixin import TimestampMixin

class User(Base, TimestampMixin):
    __tablename__ = "user"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("school.id", ondelete="CASCADE"), nullable=True)
    name = Column(String)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=True)
    mobile_no = Column(String)
    is_active = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    otp_verified = Column(Boolean, default=False)
    otp = Column(String, nullable=True)
    otp_created_at = Column(DateTime, nullable=True)
    about = Column(Text, nullable=True)
    role = Column(String, nullable=True)
    profile_img_url = Column(String, nullable=True)

    school = relationship("School", back_populates="user")
    templates = relationship("Template", back_populates="user", cascade="all, delete-orphan")
    contacts = relationship("Contact", back_populates="user", cascade="all, delete-orphan")
    message_logs = relationship("MessageLog", back_populates="user", cascade="all, delete-orphan")
    subjects = relationship("Subject", back_populates="user", cascade="all, delete-orphan")
    


class Subject(Base, TimestampMixin):
    __tablename__ = "subject"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False, index=True)

    user = relationship("User", back_populates="subjects")

    

class RefreshToken(Base, TimestampMixin):
    __tablename__ = "refresh_token"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String, nullable=False, index=True)
    token = Column(String, nullable=False)
    blacklisted = Column(Boolean, default=False)
