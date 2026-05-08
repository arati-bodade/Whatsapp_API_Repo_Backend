from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from db.base import Base


class DeviceSession(Base):
    __tablename__ = "device_sessions"

    session_id = Column(String(36), primary_key=True, index=True)
    device_id = Column(String(36), ForeignKey("devices.device_id"), nullable=False, index=True)
    session_token = Column(Text, nullable=False)  # Encrypted session data
    is_valid = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_active = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<DeviceSession(session_id={self.session_id}, device_id={self.device_id}, is_valid={self.is_valid})>"
