from sqlalchemy import Column, String, Integer, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from db.base import Base


class ResellerAnalytics(Base):
    __tablename__ = "reseller_analytics"

    id = Column(Integer, primary_key=True, index=True)
    reseller_id = Column(String(36), ForeignKey("resellers.reseller_id"), nullable=False, unique=True, index=True)
    total_credits_purchased = Column(Integer, nullable=False, default=0)
    total_credits_distributed = Column(Integer, nullable=False, default=0)
    total_credits_used = Column(Integer, nullable=False, default=0)
    remaining_credits = Column(Integer, nullable=False, default=0)
    business_user_stats = Column(JSON, nullable=False, default=list)  # Snapshotted stats
    generated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationship back to Reseller
    reseller = relationship("Reseller", back_populates="analytics")


class BusinessUserAnalytics(Base):
    __tablename__ = "business_user_analytics"

    id = Column(Integer, primary_key=True, index=True)
    reseller_id = Column(String(36), ForeignKey("resellers.reseller_id"), nullable=False, index=True)
    business_user_id = Column(String(36), ForeignKey("businesses.busi_user_id"), nullable=False, unique=True, index=True)
    business_name = Column(String, nullable=False)
    credits_allocated = Column(Integer, nullable=False, default=0)
    credits_used = Column(Integer, nullable=False, default=0)
    credits_remaining = Column(Integer, nullable=False, default=0)
    messages_sent = Column(Integer, nullable=False, default=0)
    generated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    reseller = relationship("Reseller", foreign_keys=[reseller_id])
    business_user = relationship("BusiUser", foreign_keys=[business_user_id], back_populates="analytics")
