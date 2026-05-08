from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import uuid4
from datetime import datetime
import base64
import requests

from models.message import Message, MessageStatus
from models.device import Device
from schemas.message import (
    MessageCreate, 
    MessageUpdate, 
    MessageSendRequest,
    UnifiedMessageSendRequest,
    MessageSendResponse
)


class MessageService:
    def __init__(self, db: Session):
        self.db = db

    def create_message(self, message_data: MessageCreate) -> Message:
        """Create a new message record"""
        if not message_data.message_id:
            message_data.message_id = f"msg-{uuid4().hex[:8]}"
        
        db_message = Message(**message_data.model_dump())
        self.db.add(db_message)
        self.db.commit()
        self.db.refresh(db_message)
        return db_message

    def send_unified_message(self, user_id: str, message_request: UnifiedMessageSendRequest) -> MessageSendResponse:
        """Send unified message supporting all legacy message types"""
        message_id = f"msg-{uuid4().hex[:8]}"
        
        # Get device information
        device = self.db.query(Device).filter(Device.device_id == message_request.device_id).first()
        if not device:
            raise ValueError(f"Device {message_request.device_id} not found")
        
        # Determine message content based on type
        message_body = message_request.message
        receiver_number = message_request.to
        
        # Handle different message types
        if message_request.type == "MEDIA" and message_request.media_url:
            message_body = f"[MEDIA] {message_request.media_url}"
            if message_request.caption:
                message_body += f" - {message_request.caption}"
        elif message_request.type == "BASE64" and message_request.base64_file:
            message_body = f"[BASE64_FILE] {message_request.base64_file[:50]}..."
            if message_request.caption:
                message_body += f" - {message_request.caption}"
        elif message_request.type == "TEMPLATE":
            message_body = f"[TEMPLATE] {message_request.template_name}"
            if message_request.message:
                message_body += f" - {message_request.message}"
        
        # Create message record
        message_data = MessageCreate(
            message_id=message_id,
            user_id=user_id,
            sender_number=device.phone_number,
            receiver_number=receiver_number,
            message_type=message_request.type,
            template_name=message_request.template_name,
            message_body=message_body,
            mode=message_request.mode,
            status=MessageStatus.SENT,
            credits_used=self._calculate_credits(message_request.type)
        )
        
        # Save to database
        db_message = self.create_message(message_data)
        
        # Send to WhatsApp (mock implementation)
        self._send_to_whatsapp(device, message_request, message_id)
        
        return MessageSendResponse(
            message_id=message_id,
            status=MessageStatus.SENT,
            credits_used=message_data.credits_used,
            sent_at=datetime.utcnow(),
            device_id=message_request.device_id,
            recipient=message_request.to
        )

    def _calculate_credits(self, message_type: str) -> int:
        """Calculate credits based on message type"""
        credit_map = {
            "TEXT": 1,
            "MEDIA": 2,
            "TEMPLATE": 1,
            "BASE64": 3
        }
        return credit_map.get(message_type, 1)

    def _send_to_whatsapp(self, device: Device, message_request: UnifiedMessageSendRequest, message_id: str):
        """Send message to WhatsApp (mock implementation)"""
        # This would integrate with actual WhatsApp API
        # For now, we'll simulate the send
        logger.info(f"Sending message {message_id} via device {device.device_id}")
        
        # Mock webhook call
        if message_request.is_group:
            logger.info(f"Sending to group: {message_request.to}")
        else:
            logger.info(f"Sending to individual: {message_request.to}")

    def send_message(self, user_id: str, message_request: MessageSendRequest) -> Message:
        """Send a message and create record (legacy method)"""
        message_id = f"msg-{uuid4().hex[:8]}"
        
        message_data = MessageCreate(
            message_id=message_id,
            user_id=user_id,
            sender_number="+918888888888",  # This should come from user's configured number
            receiver_number=message_request.receiver_number,
            message_type=message_request.message_type,
            template_name=message_request.template_name,
            message_body=message_request.message_body,
            mode=message_request.mode,
            status=MessageStatus.SENT
        )
        
        return self.create_message(message_data)

    def get_message_by_id(self, message_id: str) -> Optional[Message]:
        """Get message by ID"""
        return self.db.query(Message).filter(Message.message_id == message_id).first()

    def get_messages_by_user(
        self, 
        user_id: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Message]:
        """Get messages for a specific user with pagination"""
        return (
            self.db.query(Message)
            .filter(Message.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update_message_status(
        self, 
        message_id: str, 
        status: MessageStatus
    ) -> Optional[Message]:
        """Update message status"""
        message = self.get_message_by_id(message_id)
        if message:
            message.status = status
            self.db.commit()
            self.db.refresh(message)
        return message

    def update_message(
        self, 
        message_id: str, 
        update_data: MessageUpdate
    ) -> Optional[Message]:
        """Update message details"""
        message = self.get_message_by_id(message_id)
        if message:
            for field, value in update_data.model_dump(exclude_unset=True).items():
                setattr(message, field, value)
            self.db.commit()
            self.db.refresh(message)
        return message

    def delete_message(self, message_id: str) -> bool:
        """Delete a message"""
        message = self.get_message_by_id(message_id)
        if message:
            self.db.delete(message)
            self.db.commit()
            return True
        return False

    def get_message_count_by_user(self, user_id: str) -> int:
        """Get total message count for a user"""
        return (
            self.db.query(Message)
            .filter(Message.user_id == user_id)
            .count()
        )
