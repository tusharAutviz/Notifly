from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.base import Base
from app.db.base_mixin import TimestampMixin

class MessageLog(Base, TimestampMixin):
    __tablename__ = "message_logs"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    message_type = Column(String, nullable=False)  # 'email' or 'sms'
    recipient = Column(String, nullable=False, index=True)
    recipient_name = Column(String, nullable=False, index=True)
    subject = Column(String, nullable=True)
    content = Column(Text, nullable=False)
    status = Column(Boolean, default=False, index=True)

    user = relationship("User", back_populates="message_logs")
    
