from sqlalchemy import Column, String, DateTime, Integer, Float, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from db.base import Base
import uuid

class PaymentOrder(Base):
    __tablename__ = "payment_orders"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    txnid = Column(String(100), unique=True, nullable=False, index=True)
    user_id = Column(String(36), nullable=False)
    user_type = Column(String(20), nullable=False) # 'business' or 'reseller'
    # Optional: if reseller buys for a specific business user, track here
    allocated_to_user_id = Column(String(36), nullable=True)  # busi_user_id to allocate credits to
    is_allocated = Column(String(20), default="pending")  # pending, allocated
    
    plan_name = Column(String(100), nullable=False)
    credits = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String(20), default="pending") # pending, success, failed, bounced
    
    razorpay_order_id = Column(String(100), nullable=True)
    razorpay_payment_id = Column(String(100), nullable=True)
    razorpay_signature = Column(String(255), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<PaymentOrder(txnid={self.txnid}, amount={self.amount}, status={self.status})>"
