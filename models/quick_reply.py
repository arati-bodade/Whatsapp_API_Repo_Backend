import uuid
from sqlalchemy import Column, String, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from db.base import Base

class QuickReply(Base):
    __tablename__ = "quick_replies"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    busi_user_id = Column(String(36), ForeignKey("businesses.busi_user_id"), nullable=False)
    shortcut = Column(String, nullable=False) 
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
