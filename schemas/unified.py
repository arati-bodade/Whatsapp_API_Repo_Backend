from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Union
from datetime import datetime
from enum import Enum
from uuid import UUID


class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    BASE64 = "base64"


class LoginRequest(BaseModel):
    """User login request"""
    phone_number: str = Field(..., description="Phone number with country code")
    device_id: Optional[str] = Field(None, description="Device ID to use")
    whatsapp_mode: str = Field("unofficial", description="WhatsApp mode: official/unofficial")


class LoginResponse(BaseModel):
    """Login response"""
    success: bool
    message: str
    device_id: Optional[str] = None
    qr_code: Optional[str] = None
    session_status: Optional[str] = None
    access_token: Optional[str] = None


class DeviceRegisterRequest(BaseModel):
    """Device registration request"""
    device_name: str = Field(..., description="Device name")
    device_type: str = Field(..., description="Device type: mobile/desktop/web")
    phone_number: Optional[str] = Field(None, description="Phone number associated with device")


class DeviceResponse(BaseModel):
    """Device response"""
    success: bool
    device_id: str
    device_name: str
    device_type: str
    session_status: str
    qr_last_generated: Optional[datetime] = None
    last_active: Optional[datetime] = None
    created_at: datetime


class QRCodeResponse(BaseModel):
    """QR code response"""
    success: bool
    qr_code: str
    device_id: str
    qr_last_generated: datetime
    session_status: str
    expires_at: Optional[datetime] = None


class UnifiedMessageRequest(BaseModel):
    """Unified message request supporting all message types"""
    to: str = Field(..., description="Recipient phone number or group ID")
    is_group: bool = Field(False, description="Whether recipient is a group")
    type: MessageType = Field(MessageType.TEXT, description="Message type")
    message: Optional[str] = Field(None, description="Text message content")
    media_url: Optional[str] = Field(None, description="URL to media file")
    base64_file: Optional[str] = Field(None, description="Base64 encoded file data")
    caption: Optional[str] = Field(None, description="Caption for media files")
    device_id: Optional[Union[str, UUID]] = Field(None, description="Device ID to use")
    user_id: str = Field(..., description="User ID sending the message")

    @field_validator('device_id', mode='before')
    @classmethod
    def convert_device_id(cls, v):
        """Convert UUID to string if needed, with logging for debugging"""
        if v is None:
            return v
        
        if isinstance(v, UUID):
            str_value = str(v)
            print(f"DEBUG: Converting device_id UUID to string: {v} -> {str_value}")
            return str_value
        
        if isinstance(v, str):
            print(f"DEBUG: device_id already string: {v}")
            return v
        
        # Handle any other type by converting to string
        str_value = str(v)
        print(f"DEBUG: Converting device_id {type(v)} to string: {v} -> {str_value}")
        return str_value


class UnifiedMessageResponse(BaseModel):
    """Unified message response"""
    success: bool
    message_id: str
    status: str
    recipient: str
    is_group: bool
    message_type: MessageType
    sent_at: datetime
    credits_used: int
    file_url: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None


class MessageStatusUpdate(BaseModel):
    """Message status update"""
    status: str = Field(..., description="New status: sent/delivered/read/failed")
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    failed_reason: Optional[str] = None


class GroupInfo(BaseModel):
    """Group information"""
    group_id: str
    group_name: str
    group_description: Optional[str] = None
    participant_count: int
    created_at: Optional[datetime] = None
    is_admin: bool = False


class GroupMember(BaseModel):
    """Group member information"""
    phone_number: str
    name: Optional[str] = None
    is_admin: bool = False
    joined_at: Optional[datetime] = None


class WebhookMessage(BaseModel):
    """Webhook message payload"""
    message_id: str
    from_number: str
    to_number: str
    message_type: str
    message_content: Optional[str] = None
    media_url: Optional[str] = None
    timestamp: datetime
    status: str
    device_id: str

    @field_validator('timestamp', mode='before')
    @classmethod
    def parse_timestamp(cls, v):
        if isinstance(v, (int, float)):
            return datetime.fromtimestamp(v)
        return v


class WebhookStatusUpdate(BaseModel):
    """Webhook status update payload"""
    message_id: str
    status: str
    timestamp: datetime
    device_id: str
    error: Optional[str] = None

    @field_validator('timestamp', mode='before')
    @classmethod
    def parse_timestamp(cls, v):
        if isinstance(v, (int, float)):
            return datetime.fromtimestamp(v)
        return v
