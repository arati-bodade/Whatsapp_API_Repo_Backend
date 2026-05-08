from sqlalchemy import Column, String, Integer, DateTime, JSON, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from db.base import Base
import uuid

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    log_id = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True)
    
    # Reseller who "owns" or is relevant to this log
    reseller_id = Column(String(36), ForeignKey("resellers.reseller_id"), nullable=True, index=True)
    
    # User who performed the action
    performed_by_id = Column(String(36), nullable=False) # Can be reseller_id or admin_id
    performed_by_name = Column(String, nullable=False)
    performed_by_role = Column(String, nullable=False) # 'reseller', 'admin', 'system'
    
    # User affected by the action
    affected_user_id = Column(String(36), nullable=True)
    affected_user_name = Column(String, nullable=True)
    affected_user_email = Column(String, nullable=True)
    
    action_type = Column(String, nullable=False) # e.g., 'UPDATE USER PLAN', 'UPDATE USER', 'CREDIT ALLOCATION'
    module = Column(String, nullable=False) # e.g., 'Users', 'Credits', 'Reseller'
    
    description = Column(Text, nullable=True)
    changes_made = Column(JSON, nullable=True) # List of strings or dict of before/after
    
    ip_address = Column(String, nullable=True)
    user_agent = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def to_dict(self):
        return {
            "id": str(self.log_id),
            "reseller_id": str(self.reseller_id) if self.reseller_id else None,
            "performed_by": {
                "id": str(self.performed_by_id),
                "name": self.performed_by_name,
                "role": self.performed_by_role
            },
            "affected_user": {
                "id": str(self.affected_user_id) if self.affected_user_id else None,
                "name": self.affected_user_name,
                "email": self.affected_user_email
            },
            "action_type": self.action_type,
            "module": self.module,
            "description": self.description,
            "changes_made": self.changes_made,
            "ip_address": self.ip_address,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
