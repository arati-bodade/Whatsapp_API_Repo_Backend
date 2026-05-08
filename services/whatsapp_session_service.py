#!/usr/bin/env python3
"""
🔥 WHATSAPP 24-HOUR SESSION VALIDATION SERVICE

This service validates if a text message can be sent to a phone number
based on WhatsApp's 24-hour customer session rule.

✅ RULE:
- Text messages can ONLY be sent within 24 hours of customer's last message
- Template messages can be sent anytime (no session restriction)
- If no active session exists, text messages will be accepted by API but NOT delivered

❌ USAGE:
- Always validate before sending text messages
- Return clear error messages for UI display
- Log validation results for debugging
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import cast, String

from models.whatsapp_inbox import WhatsAppInbox
from models.official_whatsapp_config import OfficialWhatsAppConfig
from services.device_sync_service import ensure_device_exists

logger = logging.getLogger(__name__)

class WhatsAppSessionService:
    """
    🔥 WHATSAPP SESSION VALIDATION SERVICE
    
    Validates 24-hour customer session for text messaging.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def validate_text_message_session(
        self, 
        user_id: str, 
        phone_number: str
    ) -> Dict[str, Any]:
        """
        ✅ Validate if text message can be sent to phone number
        
        Args:
            user_id: Business user ID
            phone_number: Recipient phone number
            
        Returns:
            Dict with validation result and details
        """
        try:
            logger.info(f"🔍 SESSION VALIDATION: Checking text message session for {phone_number}")
            
            # Normalize phone number (remove +, spaces, etc)
            normalized_phone = self._normalize_phone_number(phone_number)
            
            # Find last incoming message from this phone number
            # Get user's official WhatsApp config phone_number_id (this is actually a device identifier)
            official_config = self.db.query(OfficialWhatsAppConfig).filter(
                OfficialWhatsAppConfig.busi_user_id == user_id,
                OfficialWhatsAppConfig.is_active == True
            ).first()
            
            if not official_config:
                return {
                    "can_send_text": False,
                    "reason": "no_official_config",
                    "message": "No official WhatsApp configuration found. Please configure Meta API settings first.",
                    "last_message_time": None,
                    "hours_since_last_message": None,
                    "phone_number": normalized_phone
                }
            
            # 🔥 CRITICAL: Ensure Device record exists for official WhatsApp phone_number_id
            # This fixes the UUID vs string mismatch in session validation
            device_result = ensure_device_exists(self.db, user_id, official_config.phone_number_id)
            if not device_result["success"]:
                logger.warning(f"Failed to ensure device exists for official config: {device_result.get('error')}")
                return {
                    "can_send_text": False,
                    "reason": "device_sync_error",
                    "message": f"Device synchronization error: {device_result.get('error')}",
                    "last_message_time": None,
                    "hours_since_last_message": None,
                    "phone_number": normalized_phone
                }
            
            # Use the actual device UUID from the created/found device record
            actual_device_id = device_result["device"].device_id
            
            # Use the official config's phone_number_id as the device identifier for session validation
            # Now we can safely compare UUID device_id with the ensured device record
            last_message = self.db.query(WhatsAppInbox).filter(
                WhatsAppInbox.phone_number == normalized_phone,
                WhatsAppInbox.device_id == actual_device_id
            ).order_by(WhatsAppInbox.incoming_time.desc()).first()
            
            if not last_message:
                return {
                    "can_send_text": False,
                    "reason": "no_conversation",
                    "message": "No previous conversation found with this customer. Text messages can only be sent within 24 hours of customer's last message. Please use a template message instead.",
                    "last_message_time": None,
                    "hours_since_last_message": None,
                    "phone_number": normalized_phone
                }
            
            # Calculate time since last message
            now = datetime.now(timezone.utc)
            last_message_time = last_message.incoming_time
            
            # Ensure last_message_time is timezone-aware
            if last_message_time.tzinfo is None:
                last_message_time = last_message_time.replace(tzinfo=timezone.utc)
            
            time_diff = now - last_message_time
            hours_since_last_message = time_diff.total_seconds() / 3600
            
            # Check if within 24-hour window
            if hours_since_last_message <= 24:
                return {
                    "can_send_text": True,
                    "reason": "active_session",
                    "message": f"Active customer session found. Last message received {hours_since_last_message:.1f} hours ago.",
                    "last_message_time": last_message_time.isoformat(),
                    "hours_since_last_message": round(hours_since_last_message, 1),
                    "phone_number": normalized_phone
                }
            else:
                return {
                    "can_send_text": False,
                    "reason": "session_expired",
                    "message": f"Customer session expired. Last message was {hours_since_last_message:.1f} hours ago (24-hour window). Please use a template message instead.",
                    "last_message_time": last_message_time.isoformat(),
                    "hours_since_last_message": round(hours_since_last_message, 1),
                    "phone_number": normalized_phone
                }
                
        except Exception as e:
            logger.error(f"❌ SESSION VALIDATION ERROR: {str(e)}")
            return {
                "can_send_text": False,
                "reason": "validation_error",
                "message": f"Unable to validate customer session: {str(e)}",
                "last_message_time": None,
                "hours_since_last_message": None,
                "phone_number": phone_number
            }
    
    def validate_text_messages_batch(
        self, 
        user_id: str, 
        phone_numbers: list[str]
    ) -> Dict[str, Any]:
        """
        ✅ Validate text message session for multiple phone numbers
        
        Args:
            user_id: Business user ID
            phone_numbers: List of recipient phone numbers
            
        Returns:
            Dict with batch validation results
        """
        try:
            results = []
            can_send_all = True
            
            for phone_number in phone_numbers:
                validation = self.validate_text_message_session(user_id, phone_number)
                results.append(validation)
                
                if not validation["can_send_text"]:
                    can_send_all = False
            
            # Summary statistics
            valid_sessions = sum(1 for r in results if r["can_send_text"])
            invalid_sessions = len(results) - valid_sessions
            
            return {
                "can_send_all": can_send_all,
                "total_numbers": len(phone_numbers),
                "valid_sessions": valid_sessions,
                "invalid_sessions": invalid_sessions,
                "results": results,
                "summary": self._generate_batch_summary(results)
            }
            
        except Exception as e:
            logger.error(f"❌ BATCH SESSION VALIDATION ERROR: {str(e)}")
            return {
                "can_send_all": False,
                "total_numbers": len(phone_numbers),
                "valid_sessions": 0,
                "invalid_sessions": len(phone_numbers),
                "results": [],
                "summary": f"Batch validation failed: {str(e)}"
            }
    
    def _normalize_phone_number(self, phone_number: str) -> str:
        """
        Normalize phone number for consistent lookup
        """
        # Remove +, spaces, dashes, parentheses
        normalized = phone_number.replace("+", "").replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        
        # No longer automatically prepends '91'.
        # Callers are responsible for providing the full number including country code.
        return normalized
    
    def _generate_batch_summary(self, results: list[Dict[str, Any]]) -> str:
        """
        Generate human-readable summary for batch validation
        """
        if not results:
            return "No phone numbers to validate"
        
        valid_count = sum(1 for r in results if r["can_send_text"])
        total_count = len(results)
        
        if valid_count == total_count:
            return f"✅ All {total_count} recipients have active customer sessions"
        elif valid_count == 0:
            return f"❌ None of the {total_count} recipients have active customer sessions"
        else:
            return f"⚠️ {valid_count} of {total_count} recipients have active customer sessions"

# Global function for easy access
def validate_whatsapp_text_session(
    db: Session,
    user_id: str,
    phone_number: str
) -> Dict[str, Any]:
    """
    ✅ Validate WhatsApp text message session
    
    This is the main function that should be called before sending text messages.
    """
    service = WhatsAppSessionService(db)
    return service.validate_text_message_session(user_id, phone_number)
