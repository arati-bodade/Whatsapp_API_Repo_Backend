from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class LoginRequest(BaseModel):
    """Login request schema"""
    phone_number: str = Field(..., description="Phone number with country code")
    device_id: Optional[str] = Field(None, description="Device ID to use")
    whatsapp_mode: str = Field("unofficial", description="WhatsApp mode: official/unofficial")


class LoginResponse(BaseModel):
    """Login response schema"""
    success: bool
    message: str
    device_id: Optional[str] = None
    qr_code: Optional[str] = None
    session_status: Optional[str] = None
    access_token: Optional[str] = None


class MessageRequest(BaseModel):
    """Message request schema"""
    receiver_number: str = Field(..., description="Receiver phone number with country code")
    message_text: str = Field(..., description="Message content")
    user_id: str = Field(..., description="User ID sending the message")
    device_id: Optional[str] = Field(None, description="Device ID to use")


class MessageResponse(BaseModel):
    """Message response schema"""
    success: bool
    message_id: str
    status: str
    receiver_number: str
    sent_at: datetime
    credits_used: int = 1


class FileMessageRequest(BaseModel):
    """File message request schema"""
    receiver_number: str = Field(..., description="Receiver phone number with country code")
    file_url: str = Field(..., description="File URL or base64 data")
    file_name: Optional[str] = Field(None, description="File name")
    caption: Optional[str] = Field(None, description="File caption")
    reseller_id: str = Field(..., description="Reseller ID sending the message")
    device_id: Optional[str] = Field(None, description="Device ID to use")


class FileMessageResponse(BaseModel):
    """File message response schema"""
    success: bool
    message_id: str
    status: str
    receiver_number: str
    file_url: str
    file_name: str
    file_size: Optional[int] = None
    sent_at: datetime
    credits_used: int = 2


class GroupMessageRequest(BaseModel):
    """Group message request schema"""
    group_id: str = Field(..., description="WhatsApp group ID")
    message_text: str = Field(..., description="Message content")
    reseller_id: str = Field(..., description="Reseller ID sending the message")
    device_id: Optional[str] = Field(None, description="Device ID to use")


class GroupMessageResponse(BaseModel):
    """Group message response schema"""
    success: bool
    message_id: str
    group_id: str
    group_name: Optional[str] = None
    status: str
    sent_at: datetime
    credits_used: int = 1


class DeliveryReportResponse(BaseModel):
    """Delivery report response schema"""
    message_id: str
    status: str
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    failed_reason: Optional[str] = None
    receiver_number: str


class QRCodeResponse(BaseModel):
    """QR code response schema"""
    success: bool
    qr_code: str
    device_id: str
    qr_last_generated: datetime
    session_status: str
    expires_at: Optional[datetime] = None


class DeviceRequest(BaseModel):
    """Device request schema"""
    device_name: str = Field(..., description="Device name")
    device_type: str = Field(..., description="Device type: mobile/desktop/web")
    user_id: str = Field(..., description="Business User ID owning the device")
    phone_number: Optional[str] = Field(None, description="Phone number associated with device")


class DeviceResponse(BaseModel):
    """Device response schema"""
    success: bool
    device_id: str
    device_name: str
    device_type: str
    session_status: str
    qr_last_generated: Optional[datetime] = None
    last_active: Optional[datetime] = None
    created_at: datetime


class GroupInfo(BaseModel):
    """Group information schema"""
    group_id: str
    group_name: str
    group_description: Optional[str] = None
    participant_count: int
    created_at: Optional[datetime] = None
    is_admin: bool = False


class GroupMember(BaseModel):
    """Group member schema"""
    phone_number: str
    name: Optional[str] = None
    is_admin: bool = False
    joined_at: Optional[datetime] = None


class WhatsAppStatus(str, Enum):
    """WhatsApp connection status"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    QR_GENERATED = "qr_generated"
    LOGGED_OUT = "logged_out"
    ERROR = "error"


class MessageStatus(str, Enum):
    """Message status"""
    PENDING = "PENDING"
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    READ = "READ"
    FAILED = "FAILED"


class FileType(str, Enum):
    """Supported file types"""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    STICKER = "sticker"
