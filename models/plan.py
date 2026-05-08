from sqlalchemy import Column, String, Float, Integer, UUID as SQL_UUID
from sqlalchemy.sql import func
from sqlalchemy import DateTime
import uuid
from db.base import Base

class Plan(Base):
    __tablename__ = "plans"

    plan_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=True)
    price = Column(Float, default=0.0)
    credits_offered = Column(Integer, default=0)
    validity_days = Column(Integer, default=30)
    
    # NEW: Locked Rate & Category
    deduction_value = Column(Float, default=1.0)  # Standard 1 credit per message
    plan_category = Column(String(50), default="BUSINESS")  # "BUSINESS" or "RESELLER"
    
    status = Column(String(20), default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Plan(name={self.name}, category={self.plan_category}, rate={self.deduction_value})>"
