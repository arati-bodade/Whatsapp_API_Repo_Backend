from sqlalchemy import Column, String, Integer, DateTime, Float, ForeignKey, Text, Enum
from sqlalchemy.sql import func
from db.base import Base
import uuid
import enum

class AlertSeverity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class AlertStatus(str, enum.Enum):
    UNRESOLVED = "UNRESOLVED"
    RESOLVED = "RESOLVED"

class ResellerAlert(Base):
    __tablename__ = "reseller_alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True)
    
    reseller_id = Column(String(36), ForeignKey("resellers.reseller_id"), nullable=False, index=True)
    sub_user_id = Column(String(36), nullable=False, index=True)
    sub_user_name = Column(String, nullable=False)
    
    plan_name = Column(String, nullable=False)
    required_credits = Column(Float, nullable=False)
    available_credits = Column(Float, nullable=False)
    shortage = Column(Float, nullable=False)
    
    severity = Column(String(20), default="MEDIUM") # LOW, MEDIUM, HIGH, CRITICAL
    status = Column(String(20), default="UNRESOLVED") # UNRESOLVED, RESOLVED
    
    attempt_count = Column(Integer, default=1)
    last_attempt_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def to_dict(self):
        return {
            "alert_id": self.alert_id,
            "reseller_id": self.reseller_id,
            "sub_user_id": self.sub_user_id,
            "sub_user_name": self.sub_user_name,
            "plan_name": self.plan_name,
            "required_credits": self.required_credits,
            "available_credits": self.available_credits,
            "shortage": self.shortage,
            "severity": self.severity,
            "status": self.status,
            "attempt_count": self.attempt_count,
            "last_attempt_at": self.last_attempt_at.isoformat() if self.last_attempt_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
