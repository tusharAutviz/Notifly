from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.db.base_mixin import TimestampMixin

class Contact(Base, TimestampMixin):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    student_name = Column(String, nullable=False, index=True)
    parent_name = Column(String, nullable=False)
    parent_email = Column(String, nullable=True)
    parent_phone_no = Column(String, nullable=True)
    mode = Column(String, nullable=False)

    user = relationship("User", back_populates="contacts")