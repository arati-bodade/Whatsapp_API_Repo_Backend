from sqlalchemy import Column, String, Integer, DateTime, Text, Enum, Boolean, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import validates, relationship
from enum import Enum as PyEnum
from db.base import Base
import uuid



class DeviceType(str, PyEnum):
    # 🔥 MATCHING POSTGRESQL ENUM VALUES EXACTLY
    web = "web"          # WhatsApp Web/QR devices (unofficial)
    mobile = "mobile"    # Mobile devices (if applicable)
    desktop = "desktop"  # Desktop devices (if applicable)
    official = "official"  # Official WhatsApp Cloud API devices
    
    # For backward compatibility - map to actual DB values
    @property
    def is_unofficial(self):
        return self.value in ["web", "mobile", "desktop"]
    
    @property
    def is_official(self):
        return self.value == "official"


class SessionStatus(str, PyEnum):
    created = "created"          # Device record created, no QR yet
    qr_ready = "qr_ready"        # QR code fetched from engine, ready to scan
    qr_generated = "qr_generated" # Alias for qr_ready, used in DB migration
    connected = "connected"      # Authenticated and syncing
    disconnected = "disconnected" # Disconnected by checking or engine
    connecting = "connecting"    # Currently attempting to connect
    pending = "pending"          # Legacy state, aliases to created
    expired = "expired"          # QR expired
    orphaned = "orphaned"        # DB exists, Engine session gone
    disabled = "disabled"        # Manually disabled
    logged_out = "logged_out"    # Explicitly logged out (terminal state)
    
    @classmethod
    def get_valid_values(cls):
        """Get all valid enum values for validation"""
        return [status.value for status in cls]
    
    @classmethod
    def is_valid(cls, value):
        """Check if a value is a valid enum"""
        return value in cls.get_valid_values()
    
    @classmethod
    def get_frontend_mapping(cls):
        """Map backend enum values to frontend expected values"""
        return {
            "created": "created",
            "qr_ready": "qr_generated",  # Frontend expects qr_generated
            "qr_generated": "qr_generated",
            "connected": "connected",
            "disconnected": "disconnected",
            "connecting": "connecting",
            "pending": "pending",
            "expired": "expired",
            "orphaned": "orphaned",
            "disabled": "disabled",
            "logged_out": "logged_out"
        }


class Device(Base):
    __tablename__ = "devices"
    __table_args__ = (
        UniqueConstraint('busi_user_id', 'device_name', name='uniq_user_device_name'),
    )

    device_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True, unique=True)
    busi_user_id = Column(String(36), nullable=False, index=True)
    device_name = Column(String(255), nullable=False)
    device_type = Column(Enum(DeviceType, name="devicetype", native_enum=True), nullable=False)
    
    # Add validation for enum values
    @validates('device_type')
    def validate_device_type(self, key, value):
        if isinstance(value, str):
            # Convert string to enum if valid
            try:
                return DeviceType(value)
            except ValueError:
                valid_values = [dt.value for dt in DeviceType]
                raise ValueError(f"Invalid device_type '{value}'. Valid values: {valid_values}")
        elif isinstance(value, DeviceType):
            return value
        else:
            raise ValueError(f"device_type must be string or DeviceType enum, got {type(value)}")
    session_status = Column(Enum(SessionStatus, name="sessionstatus", native_enum=True), nullable=False, default=SessionStatus.pending)
    
    # Add validation for session_status values
    @validates('session_status')
    def validate_session_status(self, key, value):
        if isinstance(value, str):
            # Convert string to enum if valid
            try:
                return SessionStatus(value)
            except ValueError:
                valid_values = SessionStatus.get_valid_values()
                raise ValueError(f"Invalid session_status '{value}'. Valid values: {valid_values}")
        elif isinstance(value, SessionStatus):
            return value
        else:
            raise ValueError(f"session_status must be string or SessionStatus enum, got {type(value)}")
    qr_last_generated = Column(DateTime(timezone=True), nullable=True)
    qr_code = Column(Text, nullable=True)  # 🔥 ADDED: Live QR storage
    ip_address = Column(String(45), nullable=True)
    last_active = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)  # Soft delete flag
    disconnected_at = Column(DateTime(timezone=True), nullable=True)  # Track when device was logged out
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # 🔥 ADDED: Permanent deletion flag
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    whatsapp_messages = relationship("WhatsAppMessages", back_populates="device", cascade="all, delete-orphan")
    whatsapp_inbox = relationship("WhatsAppInbox", back_populates="device", cascade="all, delete-orphan")
    sessions = relationship("DeviceSession", backref="device", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Device(id={self.device_id}, status={self.session_status}, type={self.device_type})>"
