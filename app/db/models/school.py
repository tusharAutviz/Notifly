from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.db.base_mixin import TimestampMixin


class School(Base, TimestampMixin):
    __tablename__ = "school"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    school_name = Column(String, nullable=False, unique=True)
    address = Column(Text, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    country = Column(String, nullable=True)
    pincode = Column(String, nullable=True)
    phone_no = Column(String, nullable=True)
    email = Column(String, nullable=True)
    website = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)

    user = relationship("User", back_populates="school", cascade="all, delete-orphan")