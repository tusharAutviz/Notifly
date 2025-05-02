from app.db.base import Base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.base_mixin import TimestampMixin

class Template(Base, TimestampMixin):
    __tablename__ = "templates"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False, unique=True)
    content = Column(Text, nullable=False)
    type = Column(String, default="email")
    subject = Column(String, nullable=True)

    user = relationship("User", back_populates="templates")