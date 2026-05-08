from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from datetime import datetime
from uuid import UUID

class PerformedBy(BaseModel):
    id: str
    name: str
    role: str

class AffectedUser(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None

class AuditLogSchema(BaseModel):
    id: str
    reseller_id: Optional[str] = None
    performed_by: PerformedBy
    affected_user: Optional[AffectedUser] = None
    action_type: str
    module: str
    description: Optional[str] = None
    changes_made: Optional[Any] = None
    ip_address: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class AuditLogCreate(BaseModel):
    reseller_id: Optional[UUID] = None
    performed_by_id: UUID
    performed_by_name: str
    performed_by_role: str
    affected_user_id: Optional[UUID] = None
    affected_user_name: Optional[str] = None
    affected_user_email: Optional[str] = None
    action_type: str
    module: str
    description: Optional[str] = None
    changes_made: Optional[Any] = None
    ip_address: Optional[str] = None

class AuditLogResponse(BaseModel):
    total: int
    filtered: int
    last_activity_days_ago: int
    logs: List[AuditLogSchema]
