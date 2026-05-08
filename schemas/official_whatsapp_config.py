from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime


class WhatsAppOfficialConfig(BaseModel):
    business_number: str = Field(..., description="Official WhatsApp business phone number")
    waba_id: str = Field(..., description="WhatsApp Business Account ID")
    phone_number_id: str = Field(..., description="Phone number ID from Meta")
    access_token: str = Field(..., description="Meta access token for API")
    template_status: str = Field(..., description="Template approval status")


class OfficialWhatsAppConfigBase(BaseModel):
    busi_user_id: str = Field(..., description="UUID of the business user")
    whatsapp_official: WhatsAppOfficialConfig


class OfficialWhatsAppConfigCreate(OfficialWhatsAppConfigBase):
    created_at: Optional[datetime] = None


class OfficialWhatsAppConfigResponse(OfficialWhatsAppConfigBase):
    id: int
    created_at: datetime
    updated_at: datetime
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class OfficialWhatsAppConfigUpdate(BaseModel):
    whatsapp_official: Optional[WhatsAppOfficialConfig] = None
    is_active: Optional[bool] = None


class WhatsAppTemplateBase(BaseModel):
    template_name: str
    template_status: str
    category: str
    language: str
    content: str
    meta_template_id: Optional[str] = None


class WhatsAppTemplateCreate(WhatsAppTemplateBase):
    busi_user_id: str


class WhatsAppTemplateResponse(WhatsAppTemplateBase):
    id: int
    busi_user_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WhatsAppTemplateValidation(BaseModel):
    template_name: str = Field(..., description="Template name")
    template_status: str = Field(..., description="Template status")
    category: str = Field(..., description="Template category")
    language: str = Field(..., description="Template language")


class WhatsAppWebhookConfig(BaseModel):
    webhook_url: str = Field(..., description="Webhook URL for receiving messages")
    verify_token: str = Field(..., description="Webhook verification token")
    webhook_version: str = Field(default="v18.0", description="WhatsApp API version")


class WhatsAppAPIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None


class WhatsAppWebhookLogResponse(BaseModel):
    id: int
    busi_user_id: str
    webhook_event: Dict[str, Any]
    event_type: str
    processed: bool
    error_message: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
