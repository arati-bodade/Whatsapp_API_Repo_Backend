from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class DeviceSessionBase(BaseModel):
    session_token: str
    expires_at: datetime
    is_valid: bool = True

class DeviceSessionCreate(DeviceSessionBase):
    device_id: str

class DeviceSessionUpdate(BaseModel):
    is_valid: Optional[bool] = None
    last_active: Optional[datetime] = None
    expires_at: Optional[datetime] = None

class DeviceSessionResponse(DeviceSessionBase):
    session_id: str
    device_id: str
    created_at: datetime
    last_active: Optional[datetime]

    class Config:
        from_attributes = True

class DeviceSessionListResponse(BaseModel):
    items: List[DeviceSessionResponse]
    total: int
    skip: int
    limit: int

class DeviceSessionValidateRequest(BaseModel):
    session_token: str

class DeviceSessionValidateResponse(BaseModel):
    is_valid: bool
    session: Optional[DeviceSessionResponse] = None
    message: Optional[str] = None

class DeviceSessionExtendRequest(BaseModel):
    hours: int = 24

class DeviceSessionExtendResponse(BaseModel):
    success: bool
    new_expires_at: datetime
    message: str
