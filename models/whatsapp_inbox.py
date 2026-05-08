import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from db.base import Base

class WhatsAppInbox(Base):
    __tablename__ = "whatsapp_inbox"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    device_id = Column(String(36), ForeignKey("devices.device_id"), nullable=False)
    phone_number = Column(String, nullable=False)  # The sender's phone number
    contact_name = Column(String, nullable=True)  # Contact name from push_name
    chat_type = Column(String, default='individual')  # Chat type: 'individual' or 'group'
    incoming_message = Column(Text, nullable=True) # Text content of the message
    message_id = Column(String, nullable=True)  # WhatsApp message ID from engine
    incoming_time = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    is_read = Column(Boolean, default=False)
    is_replied = Column(Boolean, default=False)
    is_outgoing = Column(Boolean, default=False)  # True for messages WE sent
    reply_message = Column(Text, nullable=True)
    reply_time = Column(DateTime(timezone=True), nullable=True)
    remote_jid = Column(String, nullable=True)  # Store the full WhatsApp JID (e.g., number@s.whatsapp.net)

    # Relationship
    device = relationship("Device", back_populates="whatsapp_inbox")
