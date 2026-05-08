from sqlalchemy import Column, String, Integer, DateTime, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from db.base import Base
import uuid


class MessageUsageCreditLog(Base):
    __tablename__ = "message_usage_credit_logs"

    usage_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    busi_user_id = Column(String(36), ForeignKey("businesses.busi_user_id"), nullable=False, index=True)
    message_id = Column(String(255), nullable=True, index=True) # Changed from UUID/FK to String to support Payments/Plans
    credits_deducted = Column(Float, nullable=False)
    balance_after = Column(Float, nullable=False)
    source = Column(String(50), nullable=True, default="single") # Track: single, bulk, trigger
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
