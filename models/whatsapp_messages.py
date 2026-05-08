import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from db.base import Base

class WhatsAppMessages(Base):
    """
    Production-ready WhatsApp messages table for CRM inbox system.
    Handles message synchronization from Baileys WhatsApp Web API engine.
    """
    __tablename__ = "whatsapp_messages"

    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Device association
    device_id = Column(String(36), ForeignKey("devices.device_id"), nullable=False)
    
    # Message identifiers
    message_id = Column(String(255), nullable=False, unique=True)  # WhatsApp message ID from engine
    remote_jid = Column(String(255), nullable=True)  # Full WhatsApp JID (e.g., number@s.whatsapp.net)
    
    # Contact information
    phone = Column(String(20), nullable=False)  # Clean phone number
    contact_name = Column(String(255), nullable=True)  # Contact name from push_name
    
    # Message content
    message = Column(Text, nullable=False)  # Message text content
    message_type = Column(String(50), default="text")  # text, image, document, etc.
    
    # Message metadata
    timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    from_me = Column(Boolean, nullable=False, default=False)  # True if sent by us
    
    # Read status
    is_read = Column(Boolean, nullable=False, default=False)
    
    # Additional metadata for enhanced functionality
    chat_type = Column(String(20), default="individual")  # individual, group
    media_url = Column(Text, nullable=True)  # URL for media files
    thumbnail_url = Column(Text, nullable=True)  # Thumbnail URL
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    device = relationship("Device", back_populates="whatsapp_messages")

    # Define indexes for optimal query performance
    __table_args__ = (
        # Primary index for message deduplication
        Index('idx_whatsapp_messages_message_id', 'message_id'),
        
        # Device isolation index
        Index('idx_whatsapp_messages_device_id', 'device_id'),
        
        # Phone number index for conversation grouping
        Index('idx_whatsapp_messages_phone', 'phone'),
        
        # Composite index for inbox queries (device + phone + timestamp)
        Index('idx_whatsapp_messages_device_phone_time', 'device_id', 'phone', 'timestamp'),
        
        # Unread messages index
        Index('idx_whatsapp_messages_unread', 'device_id', 'is_read', 'from_me', 'timestamp'),
        
        # Chat type index
        Index('idx_whatsapp_messages_chat_type', 'chat_type'),
        
        # Remote JID index for WhatsApp-specific queries
        Index('idx_whatsapp_messages_remote_jid', 'remote_jid'),
    )

    def __repr__(self):
        return f"<WhatsAppMessages(id={self.id}, device_id={self.device_id}, phone={self.phone}, from_me={self.from_me})>"

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': str(self.id),
            'device_id': str(self.device_id),
            'message_id': self.message_id,
            'remote_jid': self.remote_jid,
            'phone': self.phone,
            'contact_name': self.contact_name,
            'message': self.message,
            'message_type': self.message_type,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'from_me': self.from_me,
            'is_read': self.is_read,
            'chat_type': self.chat_type,
            'media_url': self.media_url,
            'thumbnail_url': self.thumbnail_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

# Add reverse relationship to Device model
from models.device import Device
Device.whatsapp_messages = relationship("WhatsAppMessages", back_populates="device")
