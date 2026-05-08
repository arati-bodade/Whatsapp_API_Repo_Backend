from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from db.base import Base
import uuid


class CreditDistribution(Base):
    __tablename__ = "credit_distributions"

    distribution_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    from_reseller_id = Column(String(36), ForeignKey("resellers.reseller_id"), nullable=False)
    to_business_user_id = Column(String(36), ForeignKey("businesses.busi_user_id"), nullable=False)
    credits_shared = Column(Integer, nullable=False)
    shared_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    from_reseller = relationship("Reseller", back_populates="credit_distributions_sent")
    to_business = relationship("BusiUser", back_populates="credit_distributions_received")

    def __repr__(self):
        return f"<CreditDistribution(distribution_id={self.distribution_id}, from_reseller_id={self.from_reseller_id}, to_business_user_id={self.to_business_user_id}, credits_shared={self.credits_shared})>"
