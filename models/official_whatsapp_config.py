from sqlalchemy import Column, String, Integer, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from db.base import Base
import uuid


class OfficialWhatsAppConfig(Base):
    __tablename__ = "official_whatsapp_configs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    busi_user_id = Column(String(36), ForeignKey("businesses.busi_user_id"), nullable=False, index=True, unique=True)
    business_number = Column(String, nullable=False)
    waba_id = Column(String, nullable=False)
    phone_number_id = Column(String, nullable=False)
    access_token = Column(String, nullable=False)
    template_status = Column(String, nullable=False, default="pending")
    is_active = Column(Boolean, default=True)
    webhook_config = Column(JSON, nullable=True)
    api_settings = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class WhatsAppTemplate(Base):
    __tablename__ = "whatsapp_templates"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    busi_user_id = Column(String(36), ForeignKey("businesses.busi_user_id"), nullable=False, index=True)
    template_name = Column(String, nullable=False)
    template_status = Column(String, nullable=False)
    category = Column(String, nullable=False)
    language = Column(String, nullable=False)
    content = Column(String, nullable=False)
    meta_template_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class WhatsAppWebhookLog(Base):
    __tablename__ = "whatsapp_webhook_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    busi_user_id = Column(String(36), ForeignKey("businesses.busi_user_id"), nullable=False, index=True)
    webhook_event = Column(JSON, nullable=False)
    event_type = Column(String, nullable=False)
    processed = Column(Boolean, default=False)
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
