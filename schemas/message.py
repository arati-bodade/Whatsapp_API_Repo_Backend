from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List, Literal
from enum import Enum
from uuid import UUID


class ChannelType(str, Enum):
    WHATSAPP = "WHATSAPP"


class MessageType(str, Enum):
    TEXT = "TEXT"
    MEDIA = "MEDIA"
    TEMPLATE = "TEMPLATE"
    BASE64 = "BASE64"


class MessageMode(str, Enum):
    OFFICIAL = "OFFICIAL"
    UNOFFICIAL = "UNOFFICIAL"


class MessageStatus(str, Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    READ = "READ"
    FAILED = "FAILED"


class MessageBase(BaseModel):
    busi_user_id: UUID = Field(..., description="Business user ID")
    channel: ChannelType = Field(default=ChannelType.WHATSAPP)
    mode: MessageMode = Field(..., description="Official or unofficial WhatsApp mode")
    sender_number: str = Field(..., description="Sender phone number with country code")
    receiver_number: str = Field(..., description="Receiver phone number with country code")
    message_type: MessageType = Field(..., description="Type of message")
    template_name: Optional[str] = Field(None, description="Template name for template messages")
    message_body: str = Field(..., description="Message content")
    credits_used: int = Field(default=1, description="Credits consumed for this message")


class MessageCreate(MessageBase):
    message_id: Optional[UUID] = None
    status: Optional[MessageStatus] = None


class MessageUpdate(BaseModel):
    status: Optional[MessageStatus] = None
    message_body: Optional[str] = None


class MessageResponse(MessageBase):
    message_id: UUID
    status: MessageStatus
    sent_at: datetime
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class MessageListResponse(BaseModel):
    messages: list[MessageResponse]
    total: int
    page: int
    size: int


# Unified Message Send Schema - Supports all legacy message types
class UnifiedMessageSendRequest(BaseModel):
    to: str = Field(..., description="Recipient phone number or group ID")
    is_group: bool = Field(default=False, description="Whether sending to group")
    type: MessageType = Field(..., description="Message type: TEXT, MEDIA, TEMPLATE, BASE64")
    message: Optional[str] = Field(None, description="Text message content")
    media_url: Optional[str] = Field(None, description="URL for media files")
    base64_file: Optional[str] = Field(None, description="Base64 encoded file content")
    caption: Optional[str] = Field(None, description="Caption for media files")
    device_id: UUID = Field(..., description="Device ID to send message from")
    template_name: Optional[str] = Field(None, description="Template name for template messages")
    mode: MessageMode = Field(default=MessageMode.UNOFFICIAL, description="Official or unofficial mode")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "to": "+1234567890",
                "is_group": False,
                "type": "TEXT",
                "message": "Hello World!",
                "device_id": "device-123",
                "mode": "UNOFFICIAL"
            }
        }
    )


# Legacy MessageSendRequest for backward compatibility
class MessageSendRequest(BaseModel):
    receiver_number: str = Field(..., description="Receiver phone number with country code")
    message_type: MessageType = Field(..., description="Type of message")
    template_name: Optional[str] = Field(None, description="Template name for template messages")
    message_body: str = Field(..., description="Message content")
    mode: MessageMode = Field(..., description="Official or unofficial WhatsApp mode")


class MessageSendResponse(BaseModel):
    message_id: UUID
    status: MessageStatus
    credits_used: int
    sent_at: datetime
    device_id: UUID
    recipient: str


class GroupInfo(BaseModel):
    group_id: UUID
    group_name: str
    member_count: int
    created_at: datetime


class GroupMember(BaseModel):
    member_id: UUID
    phone_number: str
    name: Optional[str] = None
    role: str = "member"


class WebhookEvent(BaseModel):
    event_type: str
    message_id: UUID
    status: MessageStatus
    timestamp: datetime
    metadata: Optional[dict] = None


class QRCodeResponse(BaseModel):
    qr_code: Optional[str] = None
    device_id: UUID
    expires_at: Optional[datetime] = None
    status: Literal["pending", "ready", "connected", "error", "created", "qr_ready", "disconnected", "qr"]
