from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Text, Enum, func
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from db.base import Base
from sqlalchemy.dialects.postgresql import UUID

class CampaignStatus(str, enum.Enum):
    PENDING = "Pending"
    RUNNING = "Running"
    PAUSED = "Paused"
    COMPLETED = "Completed"
    FAILED = "Failed"

class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    busi_user_id = Column(String(36), ForeignKey("businesses.busi_user_id", ondelete="CASCADE"), nullable=False)
    sheet_id = Column(String(36), ForeignKey("google_sheets.id", ondelete="CASCADE"), nullable=True)
    source_file_url = Column(Text, nullable=True) # Path to uploaded CSV/Excel data source
    name = Column(String(255), nullable=True) # Optional name for convenience
    status = Column(Enum(CampaignStatus), default=CampaignStatus.PENDING)
    session_number = Column(Integer, default=1)  # 1-4
    total_recipients = Column(Integer, default=0)
    sent_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    scheduled_at = Column(DateTime(timezone=True), nullable=True) # NEW: For global scheduling
    
    media_url = Column(Text, nullable=True)
    media_type = Column(String(50), nullable=True) # image, video, document, audio
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    devices = relationship("CampaignDevice", back_populates="campaign", cascade="all, delete-orphan")
    templates = relationship("MessageTemplate", back_populates="campaign", cascade="all, delete-orphan")
    logs = relationship("MessageLog", back_populates="campaign", cascade="all, delete-orphan")
    busi_user = relationship("BusiUser")
    sheet = relationship("GoogleSheet")

class CampaignDevice(Base):
    __tablename__ = "campaign_devices"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    campaign_id = Column(String(36), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False)
    device_id = Column(String(36), ForeignKey("devices.device_id", ondelete="CASCADE"), nullable=False)

    # Relationships
    campaign = relationship("Campaign", back_populates="devices")
    device = relationship("Device")

class MessageTemplate(Base):
    __tablename__ = "message_templates"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    campaign_id = Column(String(36), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    media_url = Column(Text, nullable=True)
    media_type = Column(String(50), nullable=True) # image, video, document, audio
    delay_override = Column(Integer, nullable=True) # Delay in seconds

    # Relationships
    campaign = relationship("Campaign", back_populates="templates")

class MessageLog(Base):
    __tablename__ = "message_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    campaign_id = Column(String(36), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False)
    device_id = Column(String(36), ForeignKey("devices.device_id", ondelete="SET NULL"), nullable=True)
    recipient = Column(String(50), nullable=False)
    template_id = Column(String(36), ForeignKey("message_templates.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(255), nullable=False) # 'success', 'failed' (increased length for descriptive errors)
    retry_count = Column(Integer, default=0)
    response_time = Column(Integer, nullable=True) # In milliseconds
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    campaign = relationship("Campaign", back_populates="logs")
