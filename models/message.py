from sqlalchemy import Column, String, Integer, DateTime, Text, Enum, Float
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from enum import Enum as PyEnum
from db.base import Base
import uuid


class ChannelType(PyEnum):
    WHATSAPP = "WHATSAPP"


class MessageType(PyEnum):
    OTP = "OTP"
    TEXT = "TEXT"
    TEMPLATE = "TEMPLATE"
    MEDIA = "MEDIA"
    BASE64 = "BASE64"
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"
    DOCUMENT = "DOCUMENT"


class MessageMode(PyEnum):
    OFFICIAL = "OFFICIAL"
    UNOFFICIAL = "UNOFFICIAL"


class MessageStatus(PyEnum):
    PENDING = "PENDING"
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    READ = "READ"
    FAILED = "FAILED"


class Message(Base):
    __tablename__ = "messages"

    message_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    busi_user_id = Column(String(36), nullable=False, index=True)
    channel = Column(Enum(ChannelType), nullable=False)
    mode = Column(Enum(MessageMode), nullable=False)
    sender_number = Column(String(100), nullable=False)
    receiver_number = Column(String(50), nullable=False)
    message_type = Column(Enum(MessageType), nullable=False)
    template_name = Column(String(100), nullable=True)
    message_body = Column(Text, nullable=False)
    status = Column(Enum(MessageStatus), nullable=False, default=MessageStatus.PENDING)
    credits_used = Column(Float, nullable=False, default=1.0)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


    def __repr__(self):
        return f"<Message(id={self.message_id}, status={self.status}, type={self.message_type})>"
