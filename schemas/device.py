from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional
from enum import Enum
from uuid import UUID


class DeviceType(str, Enum):
    WEB = "web"
    MOBILE = "mobile"
    DESKTOP = "desktop"
    OFFICIAL = "official"


class SessionStatus(str, Enum):
    created = "created"
    qr_ready = "qr_ready"
    qr_generated = "qr_generated"
    connected = "connected"
    disconnected = "disconnected"
    connecting = "connecting"
    pending = "pending"
    expired = "expired"
    orphaned = "orphaned"
    disabled = "disabled"
    logged_out = "logged_out"
    error = "error"


class DeviceBase(BaseModel):
    busi_user_id: UUID = Field(..., description="Business user ID")
    device_name: str = Field(..., description="Device name (e.g., Chrome on Windows)")
    device_type: DeviceType = Field(..., description="Type of device")
    session_status: SessionStatus = Field(default=SessionStatus.pending, description="Current session status")
    qr_last_generated: Optional[datetime] = Field(None, description="Last time QR code was generated")
    ip_address: Optional[str] = Field(None, description="IP address of the device")
    last_active: Optional[datetime] = Field(None, description="Last active timestamp")


class DeviceCreate(DeviceBase):
    device_id: Optional[UUID] = None


class DeviceUpdate(BaseModel):
    device_name: Optional[str] = None
    session_status: Optional[SessionStatus] = None
    qr_last_generated: Optional[datetime] = None
    ip_address: Optional[str] = None
    last_active: Optional[datetime] = None


class DeviceResponse(DeviceBase):
    device_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_official: bool = False

    model_config = ConfigDict(from_attributes=True)


class DeviceListResponse(BaseModel):
    devices: list[DeviceResponse]
    total: int
    page: int
    size: int


class DeviceRegisterRequest(BaseModel):
    user_id: UUID = Field(..., description="Business user ID")
    device_name: str = Field(..., description="Device name")
    device_type: DeviceType = Field(default=DeviceType.WEB, description="Device type")


class DeviceRegisterResponse(BaseModel):
    device_id: UUID
    device_name: str
    device_type: DeviceType
    session_status: SessionStatus = SessionStatus.created
    qr_code: Optional[str] = None
    qr_last_generated: Optional[datetime] = None


class DeviceStatusUpdateRequest(BaseModel):
    status: SessionStatus
    ip_address: Optional[str] = None


class QRGenerateRequest(BaseModel):
    device_id: UUID = Field(..., description="Device ID to generate QR for")


class QRGenerateResponse(BaseModel):
    device_id: UUID
    qr_code: str
    qr_last_generated: datetime
    expires_at: datetime
