#!/usr/bin/env python3
"""
Backup of unified_service.py - will be used to restore the corrupted file
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from models.device import Device
from models.message import Message, MessageMode, ChannelType, MessageType as ModelMessageType, MessageStatus
from models.busi_user import BusiUser
from models.reseller import Reseller
from models.message_usage import MessageUsageCreditLog
from schemas.unified import (
    LoginRequest, LoginResponse,
    DeviceRegisterRequest, DeviceResponse,
    QRCodeResponse,
    UnifiedMessageRequest, UnifiedMessageResponse,
    MessageStatusUpdate,
    GroupInfo, GroupMember,
    WebhookMessage, WebhookStatusUpdate,
    MessageType
)
from services.whatsapp_engine_service import WhatsAppEngineService
from services.message_usage_service import MessageUsageService

logger = logging.getLogger(__name__)

class UnifiedWhatsAppService:
    """Unified WhatsApp service for both official and unofficial messaging"""
    
    def __init__(self, db: Session):
        self.db = db
        self.engine_service = WhatsAppEngineService()
        self.message_usage_service = MessageUsageService(db)
    
    def send_unified_message(self, message_data: UnifiedMessageRequest) -> UnifiedMessageResponse:
        """Send unified message with enhanced engine validation and error handling"""
        
        logger.info(f"Starting unified message send for device {message_data.device_id} to {message_data.to}")
        
        # 1. GET DEVICE
        device = self.db.query(Device).filter(Device.device_id == message_data.device_id).first()
        if not device:
            raise Exception(f"Device {message_data.device_id} not found")
        
        # 2. VALIDATE PHONE NUMBER
        receiver = message_data.to.strip()
        if not receiver or len(receiver) < 5:
            raise Exception(f"Invalid receiver number: {receiver}")
        
        if len(receiver) > 50:
            logger.warning(f"Receiver number too long: {receiver}. Truncating.")
        
        # 3. CREDIT CHECK & DEDUCTION
        credits_to_deduct = self.message_usage_service.get_deduction_rate(message_data.user_id)
        
        # 4. CREATE MESSAGE RECORD
        # Validate message_type against allowed enum values
        message_type_str = message_data.type.upper()
        allowed_types = ['OTP', 'TEXT', 'TEMPLATE', 'MEDIA', 'BASE64', 'IMAGE', 'VIDEO', 'DOCUMENT', 'AUDIO']
        
        if message_type_str not in allowed_types:
            logger.warning(f"Invalid message_type '{message_type_str}', defaulting to TEXT")
            message_type_str = 'TEXT'
        
        message = Message(
            message_id=str(uuid.uuid4()),
            busi_user_id=message_data.user_id,
            channel=ChannelType.WHATSAPP,
            mode=MessageMode.UNOFFICIAL,
            sender_number=device.device_id,
            receiver_number=receiver,
            message_body=self._build_message_body(message_data),
            message_type=message_type_str,
            status="PENDING",
            credits_used=credits_to_deduct,
            created_at=datetime.utcnow()
        )
        
        try:
            self.db.add(message)
            self.db.flush()

            # Deduct credits upfront (will be refunded if send fails)
            try:
                self.message_usage_service.deduct_credits(
                    busi_user_id=message_data.user_id,
                    message_id=message.message_id,
                    amount=credits_to_deduct
                )
            except Exception as e:
                logger.error(f"Credit deduction failed: {str(e)}")
                raise e

            # 5. SEND TO WHATSAPP ENGINE
            logger.info(f"Sending message via engine service - Device: {device.device_id}, To: {receiver}, Type: {message_data.type}")
            
            # Handle media messages
            logger.info(f"   Message type: {message_data.type}, media_url: {message_data.media_url}")
            if message_data.type != MessageType.TEXT and message_data.media_url:
                # Convert HTTP URL back to local path for engine service
                media_path = message_data.media_url
                if media_path.startswith('http://localhost:8000/uploads/'):
                    media_path = media_path.replace('http://localhost:8000/uploads/', 'uploads/')
                elif media_path.startswith('http://127.0.0.1:8000/uploads/'):
                    media_path = media_path.replace('http://127.0.0.1:8000/uploads/', 'uploads/')
                
                logger.info(f"   Sending media message via send_file_with_caption: {media_path}")
                # Send media message using send_file_with_caption
                result = self.engine_service.send_file_with_caption(
                    device_id=str(device.device_id),
                    to=receiver,
                    file_path=media_path,
                    caption=message.message_body,
                    device_name=device.device_name,
                    skip_credit_deduction=True,
                    authenticated_user_id=str(message_data.user_id)
                )
                logger.info(f"   Media send result: {result}")
            else:
                logger.info(f"   Sending text message via send_message")
                # Send text message
                result = self.engine_service.send_message(
                    device_id=str(device.device_id),
                    to=receiver,
                    message=message.message_body,
                    skip_credit_deduction=True,
                    authenticated_user_id=str(message_data.user_id)
                )
                logger.info(f"   Text send result: {result}")
            
            if result["success"]:
                message.status = "SENT"
                message.sent_at = datetime.utcnow()
                
                # Update Message ID if Baileys provided one
                new_msg_id = None
                if result.get("result") and result["result"].get("messageId"):
                    new_msg_id = result["result"]["messageId"]
                elif result.get("data") and result["data"].get("messageId"):
                    new_msg_id = result["data"]["messageId"]
                
                if new_msg_id:
                    # 🔥 UNIQUE CONSTRAINT SAFETY: Check if this ID already exists in DB
                    # If it does (e.g. duplicate from engine), keep our UUID to prevent crash
                    existing = self.db.query(Message).filter(Message.message_id == new_msg_id).first()
                    if not existing:
                        message.message_id = new_msg_id
                    else:
                        logger.warning(f"⚠️ [COLLISION_PREVENTED] Engine returned already-used ID: {new_msg_id}. Keeping internal UUID: {message.message_id}")
                
                logger.info(f"Message sent successfully to {receiver} via device {device.device_id}")
            else:
                message.status = "FAILED"
                # REFUND CREDITS if engine failed to accept
                try:
                    user = self.db.query(BusiUser).filter(BusiUser.busi_user_id == message_data.user_id).first()
                    is_res = False
                    if not user:
                        user = self.db.query(Reseller).filter(Reseller.reseller_id == message_data.user_id).first()
                        is_res = True
                    
                    if user:
                        if not is_res:
                            user.credits_remaining += credits_to_deduct
                            user.credits_used -= credits_to_deduct
                            new_bal = user.credits_remaining
                        else:
                            user.available_credits += credits_to_deduct
                            user.used_credits -= credits_to_deduct
                            new_bal = user.available_credits
                        
                        refund_log = MessageUsageCreditLog(
                            usage_id=f"refund-{uuid.uuid4().hex[:8]}",
                            busi_user_id=message_data.user_id,
                            message_id=message.message_id,
                            credits_deducted=-credits_to_deduct,
                            balance_after=new_bal,
                            timestamp=datetime.utcnow()
                        )
                        self.db.add(refund_log)
                        logger.info(f"REFUNDED {credits_to_deduct} credits to {message_data.user_id}")
                except Exception as refund_err:
                    logger.error(f"REFUND FAILED: {str(refund_err)}")
                
                error_msg = result.get("error", "Unknown error")
                logger.error(f"Engine send failed for device {device.device_id}: {error_msg}")
                raise Exception(f"WhatsApp Engine error: {error_msg}")
            
            # 6. COMMIT TRANSACTION
            self.db.commit()
            
            return UnifiedMessageResponse(
                success=True,
                message_id=str(message.message_id),
                status=message.status,
                recipient=receiver,
                is_group=message_data.is_group,
                message_type=message_data.type,
                sent_at=message.sent_at,
                credits_used=message.credits_used
            )
            
        except Exception as e:
            # ROLLBACK ON ERROR
            try:
                self.db.rollback()
                message.status = "FAILED"
                self.db.commit()
            except Exception as inner_e:
                logger.error(f"Secondary rollback error: {inner_e}")
                self.db.rollback()
            
            logger.error(f"Failed to send message to {receiver}: {e}")
            raise Exception(f"Failed to send message: {str(e)}")

    async def send_message(self, device_id: str, to: str, message: str, skip_credit_deduction: bool = False, authenticated_user_id: Optional[str] = None) -> Dict[str, Any]:
        """Send text message via engine service with phone validation"""
        logger.info(f"Sending text message to {to} via device {device_id}")
        try:
            # 1. VALIDATE PHONE NUMBER FORMAT
            from utils.validators import validate_phone
            if not validate_phone(to):
                return {"success": False, "error": f"Invalid phone number format: {to} (must be 10-15 digits)"}
            
            # 2. VALIDATE DEVICE EXISTS
            device = self.db.query(Device).filter(Device.device_id == device_id).first()
            if not device:
                return {"success": False, "error": f"Device {device_id} not found"}
            
            # 3. SEND TEXT USING ENGINE SERVICE
            result = self.engine_service.send_message(
                device_id=str(device_id),
                to=to,
                message=message,
                skip_credit_deduction=skip_credit_deduction,
                authenticated_user_id=authenticated_user_id
            )
            
            logger.info(f"Text Engine Result: {result}")
            
            # Check for non-WhatsApp registration errors
            if not result.get("success"):
                error_msg = result.get("error", "").lower()
                if "not on whatsapp" in error_msg or "not registered" in error_msg or "phone number not associated" in error_msg:
                    return {"success": False, "error": "Number not registered on WhatsApp", "not_on_whatsapp": True}
            
            return result
            
        except Exception as e:
            logger.error(f"Exception in send_message: {str(e)}")
            return {"success": False, "error": str(e)}

    async def send_media_message(self, device_id: str, to: str, caption: str, media_url: str, media_type: str = "image", skip_credit_deduction: bool = False, authenticated_user_id: Optional[str] = None) -> Dict[str, Any]:
        """Send media message via engine service with phone validation"""
        logger.info(f"Sending {media_type} message to {to} via device {device_id}")
        try:
            # 1. VALIDATE PHONE NUMBER FORMAT
            from utils.validators import validate_phone
            if not validate_phone(to):
                return {"success": False, "error": f"Invalid phone number format: {to} (must be 10-15 digits)"}
            
            # 2. VALIDATE DEVICE EXISTS
            device = self.db.query(Device).filter(Device.device_id == device_id).first()
            if not device:
                return {"success": False, "error": f"Device {device_id} not found"}
            
            # 3. SEND MEDIA USING ENGINE SERVICE
            result = self.engine_service.send_file_with_caption(
                device_id=str(device_id),
                to=to,
                file_path=media_url,
                caption=caption,
                device_name=device.device_name,
                skip_credit_deduction=skip_credit_deduction,
                authenticated_user_id=authenticated_user_id
            )
            
            logger.info(f"Media Engine Result: {result}")
            
            # Check for non-WhatsApp registration errors
            if not result.get("success"):
                error_msg = result.get("error", "").lower()
                if "not on whatsapp" in error_msg or "not registered" in error_msg or "phone number not associated" in error_msg:
                    return {"success": False, "error": "Number not registered on WhatsApp", "not_on_whatsapp": True}
            
            return result
            
        except Exception as e:
            logger.error(f"Exception in send_media_message: {str(e)}")
            return {"success": False, "error": str(e)}

    def _build_message_body(self, message_data: UnifiedMessageRequest) -> str:
        """Build message body based on type"""
        if message_data.type == MessageType.TEXT:
            return message_data.message or ""
        elif message_data.caption:
            return message_data.caption
        elif message_data.message:
            return message_data.message
        else:
            return ""

    def get_message_status(self, message_id: str, user_id: str) -> Dict[str, Any]:
        """Get message status and details"""
        try:
            message = self.db.query(Message).filter(
                Message.message_id == message_id,
                Message.busi_user_id == user_id
            ).first()
            
            if not message:
                raise Exception("Message not found")
            
            return {
                "message_id": message.message_id,
                "status": message.status,
                "receiver_number": message.receiver_number,
                "message_body": message.message_body,
                "message_type": message.message_type,
                "credits_used": message.credits_used,
                "created_at": message.created_at,
                "sent_at": message.sent_at,
                "updated_at": message.updated_at
            }
            
        except Exception as e:
            raise Exception(f"Failed to get message status: {str(e)}")

    def update_message_status(self, message_id: str, status_update: MessageStatusUpdate) -> Dict[str, str]:
        """Update message status"""
        try:
            message = self.db.query(Message).filter(Message.message_id == message_id).first()
            
            if not message:
                raise Exception("Message not found")
            
            message.status = status_update.status
            message.updated_at = datetime.utcnow()
            
            if status_update.delivered_at:
                message.sent_at = status_update.delivered_at
            if status_update.read_at:
                message.updated_at = status_update.read_at
            
            self.db.commit()
            
            return {"message": "Message status updated successfully", "status": status_update.status}
            
        except Exception as e:
            raise Exception(f"Failed to update message status: {str(e)}")

    def get_groups(self, user_id: str) -> List[GroupInfo]:
        """Get all WhatsApp groups for user"""
        try:
            # Simulate group data - in real implementation, fetch from WhatsApp API
            groups = [
                GroupInfo(
                    group_id="group1",
                    group_name="Family Group",
                    participant_count=15,
                    is_admin=True,
                    created_at=datetime.utcnow() - timedelta(days=30)
                ),
                GroupInfo(
                    group_id="group2",
                    group_name="Work Team",
                    participant_count=25,
                    is_admin=False,
                    created_at=datetime.utcnow() - timedelta(days=15)
                )
            ]
            return groups
        except Exception as e:
            raise Exception(f"Failed to get groups: {str(e)}")

    def get_group_members(self, group_id: str, user_id: str) -> List[GroupMember]:
        """Get all members of a specific group"""
        try:
            # Simulate group members data
            members = [
                GroupMember(
                    phone_number="+919876543210",
                    name="John Doe",
                    is_admin=True,
                    joined_at=datetime.utcnow() - timedelta(days=30)
                ),
                GroupMember(
                    phone_number="+919876543211",
                    name="Jane Smith",
                    is_admin=False,
                    joined_at=datetime.utcnow() - timedelta(days=25)
                )
            ]
            return members
        except Exception as e:
            raise Exception(f"Failed to get group members: {str(e)}")

    def process_webhook_message(self, webhook_data: WebhookMessage) -> Dict[str, str]:
        """Process incoming webhook message"""
        try:
            # Store incoming message
            # Validate message_type against allowed enum values
            message_type_str = webhook_data.message_type.upper()
            allowed_types = ['OTP', 'TEXT', 'TEMPLATE', 'MEDIA', 'BASE64', 'IMAGE', 'VIDEO', 'DOCUMENT', 'AUDIO']
            
            if message_type_str not in allowed_types:
                logger.warning(f"Invalid webhook message_type '{message_type_str}', defaulting to TEXT")
                message_type_str = 'TEXT'
            
            message = Message(
                message_id=webhook_data.message_id,
                busi_user_id=self._get_user_by_device(webhook_data.device_id),
                receiver_number=webhook_data.from_number,
                message_body=webhook_data.message_content,
                message_type=message_type_str,
                status=webhook_data.status,
                created_at=webhook_data.timestamp
            )
            
            self.db.add(message)
            self.db.commit()
            
            return {"message": "Webhook processed successfully"}
            
        except Exception as e:
            raise Exception(f"Failed to process webhook: {str(e)}")

    def process_webhook_status_update(self, webhook_data: WebhookStatusUpdate) -> Dict[str, str]:
        """Process webhook status update"""
        try:
            message = self.db.query(Message).filter(Message.message_id == webhook_data.message_id).first()
            
            if message:
                message.status = webhook_data.status
                message.updated_at = webhook_data.timestamp
                self.db.commit()
            
            return {"message": "Status update processed successfully"}
            
        except Exception as e:
            raise Exception(f"Failed to process webhook: {str(e)}")

    def _get_user_by_device(self, device_id: str) -> str:
        """Get user ID from device ID"""
        device = self.db.query(Device).filter(Device.device_id == device_id).first()
        return device.busi_user_id if device else "unknown"
