from sqlalchemy import Column, String, DateTime, Integer, Text, Boolean, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from db.base import Base
import uuid


class Reseller(Base):
    __tablename__ = "resellers"

    reseller_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    role = Column(String(50), nullable=False, default="reseller")
    status = Column(String(20), nullable=False, default="active")
    created_by = Column(String(36), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Profile fields
    name = Column(String(255), nullable=False)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(20), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    profile_image = Column(String(500), nullable=True)

    # Business fields
    business_name = Column(String(255), nullable=True)
    organization_type = Column(String(100), nullable=True)
    business_description = Column(Text, nullable=True)
    erp_system = Column(String(100), nullable=True)
    gstin = Column(String(20), unique=True, nullable=True)
    
    # Plan fields
    plan_id = Column(String(36), nullable=True)
    plan_name = Column(String(100), nullable=True)
    plan_expiry = Column(DateTime(timezone=True), nullable=True)

    # Address fields
    full_address = Column(Text, nullable=True)
    pincode = Column(String(10), nullable=True)
    country = Column(String(100), nullable=True)

    # Bank fields
    bank_name = Column(String(255), nullable=True)

    # Wallet fields
    total_credits = Column(Float, default=0.0)
    available_credits = Column(Float, default=0.0)
    used_credits = Column(Float, default=0.0)

    # Relationship with business users
    business_users = relationship("BusiUser", back_populates="parent_reseller")
    
    # [NEW] Relationship with active plan
    plan = relationship("Plan", primaryjoin="Reseller.plan_id == Plan.plan_id", foreign_keys="[Reseller.plan_id]")
    
    # Relationship with credit distributions sent
    credit_distributions_sent = relationship(
        "CreditDistribution", 
        back_populates="from_reseller",
        cascade="all, delete-orphan"
    )
    
    # Relationship with reseller analytics
    analytics = relationship(
        "ResellerAnalytics", 
        back_populates="reseller",
        cascade="all, delete-orphan"
    )
    
    # Remove the conflicting business_analytics relationship to avoid warnings

    def __repr__(self):
        return f"<Reseller(reseller_id={self.reseller_id}, username={self.username}, email={self.email})>"
    
    @property
    def profile(self):
        return {
            "name": self.name,
            "username": self.username,
            "email": self.email,
            "phone": self.phone,
            "profile_image": self.profile_image
        }
    
    @property
    def wallet(self):
        return {
            "total_credits": self.total_credits,
            "available_credits": self.available_credits,
            "used_credits": self.used_credits
        }
