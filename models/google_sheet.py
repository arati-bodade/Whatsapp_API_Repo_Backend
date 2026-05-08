from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Text, JSON, Enum, func
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from .base import Base
from sqlalchemy.dialects.postgresql import UUID

class SheetStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    ERROR = "ERROR"

class TriggerType(str, enum.Enum):
    NEW_ROW = "new_row"
    UPDATE_ROW = "update_row"
    TIME = "time"

class TriggerHistoryStatus(str, enum.Enum):
    PENDING = "pending"  # NEW: Message accepted, pending delivery
    SENT = "sent"
    FAILED = "failed"

class GoogleSheetTrigger(Base):
    __tablename__ = "google_sheet_triggers"

    # Match actual database schema
    trigger_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("businesses.busi_user_id", ondelete="CASCADE"), nullable=True) # NEW: Direct ownership
    sheet_id = Column(String(36), ForeignKey("google_sheets.id"), nullable=True) # Linked sheet (Optional for Files)
    device_id = Column(String(36), nullable=True)  # WhatsApp Device
    trigger_type = Column(String, nullable=False)  # DB uses character varying, not Enum
    is_enabled = Column(Boolean, default=True)
    last_triggered_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_processed_row = Column(Integer, default=0)  # Track last processed row
    
    # 🔹 D. Trigger Model FIX
    # Add missing fields:
    phone_column = Column(String, nullable=False, default="phone")
    status_column = Column(String, nullable=False, default="Status")  # NEW: Status column name
    trigger_value = Column(String, nullable=False, default="Send")   # NEW: Trigger value
    message_template = Column(Text, nullable=True)
    send_time_column = Column(String, nullable=True)  # NEW: Send_time column for time-based triggers
    message_column = Column(String, nullable=True)  # NEW: Message column to get content from sheet
    scheduled_at = Column(DateTime(timezone=True), nullable=True) # NEW: For global scheduling
    source_file_url = Column(String, nullable=True) # NEW: For file-based triggers
    media_url = Column(String, nullable=True) # NEW: For media triggers (local path or URL)
    media_type = Column(String(50), nullable=True) # NEW: image/video/audio/document
    
    # Legacy fields for compatibility
    trigger_column = Column(String, nullable=True)  # Deprecated, use status_column
    webhook_url = Column(String, nullable=True)
    trigger_config = Column(JSON, nullable=True) # Catch-all for extra config

    # Relationships
    sheet = relationship("GoogleSheet", back_populates="triggers")

class GoogleSheetTriggerHistory(Base):
    __tablename__ = "sheet_trigger_history"  # ✅ Correct table name

    # Match actual database schema
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))  # ✅ id, not history_id
    sheet_id = Column(String(36), ForeignKey("google_sheets.id"), nullable=True) # 🔥 Made nullable for file triggers
    trigger_id = Column(String(36), nullable=False)  # ✅ Added missing trigger_id field
    device_id = Column(String(36), nullable=True)  # 🔥 ADDED: Track which device sent it, converted to String
    phone_number = Column(String, nullable=False)  # ✅ phone_number, not phone
    message_content = Column(Text, nullable=False)  # ✅ message_content, not message
    status = Column(String, nullable=False)  # ✅ String, not Enum
    error_message = Column(Text, nullable=True)
    triggered_at = Column(DateTime(timezone=True), server_default=func.now())  # ✅ triggered_at, not executed_at
    row_data = Column(JSON, nullable=True)  # ✅ row_data, not individual fields

    # Relationships
    sheet = relationship("GoogleSheet", back_populates="trigger_history")

class GoogleSheet(Base):
    __tablename__ = "google_sheets"

    # Match actual database schema
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("businesses.busi_user_id"), nullable=False)
    sheet_name = Column(String, nullable=False)
    spreadsheet_id = Column(String, nullable=False)
    worksheet_name = Column(String, nullable=True)
    status = Column(Enum(SheetStatus), default=SheetStatus.ACTIVE)  # Correctly mapped to DB Enum
    total_rows = Column(Integer, default=0)
    trigger_enabled = Column(Boolean, default=True)
    message_template = Column(Text, nullable=True)
    trigger_config = Column(JSON, nullable=True)
    device_id = Column(String(36), nullable=True)  # 🔥 ADDED: Device reference, UUID type
    connected_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_synced_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    owner = relationship("BusiUser", back_populates="google_sheets")
    triggers = relationship("GoogleSheetTrigger", back_populates="sheet", cascade="all, delete-orphan")
    trigger_history = relationship("GoogleSheetTriggerHistory", back_populates="sheet", cascade="all, delete-orphan")
