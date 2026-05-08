from pydantic import BaseModel, field_validator
from typing import Optional, Union
from datetime import datetime
import uuid

class IncomingWebhookRequest(BaseModel):
    device_id: str
    phone_number: Optional[str] = None
    remote_jid: Optional[str] = None  # Full JID for proper phone number extraction
    message: Optional[str] = None
    push_name: Optional[str] = None  # Contact name from WhatsApp
    timestamp: Optional[Union[int, float]] = None 
    
    # New fields for events
    event: Optional[str] = None
    status: Optional[str] = None
    
    model_config = {"extra": "allow"} 

    @field_validator('timestamp', mode='before')
    @classmethod
    def parse_timestamp(cls, v):
        if isinstance(v, float):
            return int(v)
        return v 

class InboxMessageResponse(BaseModel):
    id: uuid.UUID
    device_id: uuid.UUID
    phone_number: str
    contact_name: Optional[str] = None  # Contact name from WhatsApp
    incoming_message: Optional[str]
    incoming_time: datetime
    is_replied: bool
    reply_message: Optional[str]
    reply_time: Optional[datetime]
    device_name: Optional[str] = None
    is_incoming: bool = True
    is_outgoing: bool = False
    unread: bool = False
    remote_jid: Optional[str] = None
    message_id: Optional[str] = None

    class Config:
        from_attributes = True

class InboxResponse(BaseModel):
    success: bool
    data: list[InboxMessageResponse]

class ReplyRequest(BaseModel):
    message_id: Optional[uuid.UUID] = None
    reply_text: str
    phone: str
    device_id: str
    remoteJid: Optional[str] = None
    jid: Optional[str] = None

class MarkReadRequest(BaseModel):
    phone_number: str
    device_id: Optional[str] = None
