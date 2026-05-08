from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from enum import Enum

class CampaignStatus(str, Enum):
    PENDING = "Pending"
    RUNNING = "Running"
    PAUSED = "Paused"
    COMPLETED = "Completed"
    FAILED = "Failed"

# --- Request Schemas ---

class MessageTemplateCreate(BaseModel):
    content: str
    media_url: Optional[str] = None
    media_type: Optional[str] = None
    delay_override: Optional[int] = None

class CampaignCreateRequest(BaseModel):
    sheet_id: Optional[UUID] = None
    source_file_url: Optional[str] = None
    name: Optional[str] = None
    device_ids: List[UUID] = Field(..., min_length=1, max_length=5)
    templates: List[MessageTemplateCreate] = Field(..., min_length=1, max_length=5)
    media_url: Optional[str] = None
    media_type: Optional[str] = None
    warm_mode: Optional[bool] = False # Informative - used in delay
    scheduled_at: Optional[datetime] = None # NEW: Global scheduling time

# --- Response Schemas ---

class CampaignDeviceResponse(BaseModel):
    id: UUID
    device_id: UUID

    model_config = ConfigDict(from_attributes=True)

class MessageTemplateResponse(BaseModel):
    id: UUID
    content: str
    media_url: Optional[str] = None
    media_type: Optional[str] = None
    delay_override: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

class MessageLogResponse(BaseModel):
    id: UUID
    device_id: Optional[UUID] = None
    recipient: str
    template_id: Optional[UUID] = None
    status: str
    retry_count: int
    response_time: Optional[int] = None
    created_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class CampaignResponse(BaseModel):
    id: UUID
    busi_user_id: UUID
    sheet_id: Optional[UUID] = None
    source_file_url: Optional[str] = None
    name: Optional[str] = None
    status: CampaignStatus
    session_number: int
    total_recipients: int
    sent_count: int
    failed_count: int
    
    scheduled_at: Optional[datetime] = None
    media_url: Optional[str] = None
    media_type: Optional[str] = None
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    devices: Optional[List[CampaignDeviceResponse]] = []
    templates: Optional[List[MessageTemplateResponse]] = []

    model_config = ConfigDict(from_attributes=True)

class CampaignProgressResponse(BaseModel):
    campaign_id: UUID
    status: CampaignStatus
    sent_count: int
    failed_count: int
    total_recipients: int
    remaining: int

class CampaignStatusResponse(BaseModel):
    status: str
    message: str
    data: Optional[CampaignResponse] = None
