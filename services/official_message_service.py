#!/usr/bin/env python3
"""
🔥 CENTRALIZED OFFICIAL WHATSAPP MESSAGE SERVICE

This service provides the SINGLE SOURCE OF TRUTH for all official WhatsApp messaging.
Used by:
- /official-message page
- Google Sheet messaging  
- Google Sheet triggers
- Any future official messaging features

✅ SUPPORTED:
- Official text messages (within 24h window)
- Official template messages
- Meta API integration
- Proper device filtering (Official API Active only)

❌ NEVER USE:
- Unofficial messaging functions
- Web/QR based engines
- Direct API calls without this service
"""

import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from sqlalchemy.orm import Session

from models.official_whatsapp_config import OfficialWhatsAppConfig
from models.device import Device
from services.official_whatsapp_config_service import OfficialWhatsAppConfigService
from services.device_sync_service import ensure_device_exists
from services.whatsapp_session_service import WhatsAppSessionService
from utils.phone_utils import normalize_phone
from services.message_usage_service import MessageUsageService

logger = logging.getLogger(__name__)

class OfficialMessageService:
    """
    🔥 CENTRALIZED OFFICIAL WHATSAPP MESSAGING SERVICE
    
    Single source of truth for all official WhatsApp messaging operations.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.official_config_service = OfficialWhatsAppConfigService(db)
        self.session_service = WhatsAppSessionService(db)
        self.message_usage_service = MessageUsageService(db)
    
    async def send_official_text_message(
        self,
        user_id: str,
        phone_number: str,
        message_text: str,
        device_id: Optional[str] = None,  # Kept for compatibility, but uses official config
        skip_credit_deduction: bool = False  # Skip credit deduction for bulk/trigger flows
    ) -> Dict[str, Any]:
        """
        ✅ Send OFFICIAL WhatsApp text message via Meta API
        
        Args:
            user_id: Business user ID
            phone_number: Recipient phone number
            message_text: Text message content
            device_id: Device ID (kept for compatibility, ignored)
            
        Returns:
            Dict with success status and Meta API response (includes wamid)
        """
        try:
            logger.info(f"🚀 OFFICIAL TEXT SEND: to {phone_number}")
            logger.info("📝 TEXT MESSAGE: Session validation REQUIRED (WhatsApp 24h rule)")
            
            # Standardize phone number format
            normalized_phone = normalize_phone(phone_number)
            if not normalized_phone:
                return {"success": False, "error": f"Invalid recipient number: {phone_number}"}
            phone_number = normalized_phone
            
            # 🔥 CRITICAL: Validate 24-hour customer session BEFORE sending
            session_validation = self.session_service.validate_text_message_session(user_id, phone_number)
            
            if not session_validation["can_send_text"]:
                logger.warning(f"❌ SESSION VALIDATION FAILED: {session_validation['message']}")
                return {
                    "success": False,
                    "error": session_validation["message"],
                    "error_type": session_validation["reason"],
                    "session_details": {
                        "can_send_text": False,
                        "last_message_time": session_validation.get("last_message_time"),
                        "hours_since_last_message": session_validation.get("hours_since_last_message")
                    }
                }
            
            logger.info(f"✅ SESSION VALIDATION PASSED: {session_validation['message']}")
            
            # Step 1: Get user's official WhatsApp config
            config = self.official_config_service.get_config_by_user_id(user_id)
            if not config:
                return {
                    "success": False,
                    "error": "Official WhatsApp configuration not found. Please configure Meta API settings first."
                }
            
            if not config.is_active:
                return {
                    "success": False,
                    "error": "Official WhatsApp configuration is not active."
                }
            
            # Step 2: Send text message via Meta API
            result = self.official_config_service.send_text_message(
                config=config,
                to_number=phone_number,
                content=message_text
            )
            
            if result.success:
                message_id = result.data.get('messages', [{}])[0].get('id')
                logger.info(f"✅ OFFICIAL TEXT SENT: wamid={message_id}")
                
                # 🔥 DEDUCT CREDITS (skip for bulk/trigger)
                if not skip_credit_deduction:
                    try:
                        self.message_usage_service.deduct_credits(
                            busi_user_id=user_id,
                            message_id=message_id,
                            amount=1,  # Official cost
                            source="single"
                        )
                        self.db.commit()
                    except Exception as credit_err:
                        logger.error(f"⚠️ Credit deduction failed but message was sent: {str(credit_err)}")
                
                return {
                    "success": True,
                    "message_id": message_id,
                    "data": result.data,
                    "message_type": "text",
                    "phone_number": phone_number
                }
            else:
                logger.error(f"❌ OFFICIAL TEXT FAILED: {result.error_message}")
                return {
                    "success": False,
                    "error": result.error_message or "Failed to send official text message"
                }
                
        except Exception as e:
            logger.error(f"❌ OFFICIAL TEXT ERROR: {str(e)}")
            return {
                "success": False,
                "error": f"Text messaging error: {str(e)}"
            }
    
    async def send_official_template_message(
        self,
        user_id: str,
        phone_number: str,
        template_name: str,
        language_code: str = "en_US",
        header_params: Optional[List[str]] = None,
        body_params: Optional[List[str]] = None,
        button_params: Optional[Dict[str, str]] = None,
        device_id: Optional[str] = None,  # Kept for compatibility, but ignored
        skip_credit_deduction: bool = False  # Skip credit deduction for bulk/trigger flows
    ) -> Dict[str, Any]:
        """
        ✅ Send OFFICIAL WhatsApp template message via Meta API
        
        Args:
            user_id: Business user ID
            phone_number: Recipient phone number
            template_name: Name of approved template
            language_code: Template language code
            header_params: List of header parameter values
            body_params: List of body parameter values  
            button_params: Dict of button parameter values
            device_id: Device ID (kept for compatibility, ignored)
            
        Returns:
            Dict with success status and Meta API response (includes wamid)
        """
        try:
            logger.info(f"🚀 OFFICIAL TEMPLATE SEND: {template_name} to {phone_number}")
            logger.info("📋 TEMPLATE MESSAGE: Session validation NOT required (WhatsApp 24h rule)")
            
            # Standardize phone number format
            normalized_phone = normalize_phone(phone_number)
            if not normalized_phone:
                return {"success": False, "error": f"Invalid recipient number: {phone_number}"}
            phone_number = normalized_phone
            
            # Step 1: Get user's official WhatsApp config
            config = self.official_config_service.get_config_by_user_id(user_id)
            if not config:
                return {
                    "success": False,
                    "error": "Official WhatsApp configuration not found. Please configure Meta API settings first."
                }
            
            if not config.is_active:
                return {
                    "success": False,
                    "error": "Official WhatsApp configuration is not active."
                }
            
            # Step 2: Validate template exists and is approved
            from models.official_whatsapp_config import WhatsAppTemplate
            template = self.db.query(WhatsAppTemplate).filter(
                WhatsAppTemplate.busi_user_id == user_id,
                WhatsAppTemplate.template_name == template_name,
                WhatsAppTemplate.template_status == "APPROVED"
            ).first()
            
            if not template:
                return {
                    "success": False,
                    "error": f"Template '{template_name}' not found or not approved. Please ensure the template exists and has APPROVED status."
                }
            
            # Step 3: Validate language (fallback to template language if mismatch)
            if template.language != language_code:
                logger.warning(f"Language mismatch for template {template_name}: requested {language_code}, available {template.language}")
                language_code = template.language  # Use template's language as fallback
            
            # Step 4: Build template components for Meta API
            template_data = self._build_template_components(
                header_params=header_params,
                body_params=body_params,
                button_params=button_params
            )
            
            # Step 5: Send via Meta API
            result = self.official_config_service.send_template_message(
                config=config,
                to_number=phone_number,
                template_name=template_name,
                template_data=template_data,
                language_code=language_code
            )
            
            if result.success:
                message_id = result.data.get('messages', [{}])[0].get('id')
                logger.info(f"✅ OFFICIAL TEMPLATE SENT: wamid={message_id}")
                
                # 🔥 DEDUCT CREDITS (skip for bulk/trigger)
                if not skip_credit_deduction:
                    try:
                        self.message_usage_service.deduct_credits(
                            busi_user_id=user_id,
                            message_id=message_id,
                            amount=1,  # Official cost (template)
                            source="single"
                        )
                        self.db.commit()
                    except Exception as credit_err:
                        logger.error(f"⚠️ Credit deduction failed but template message was sent: {str(credit_err)}")
                
                return {
                    "success": True,
                    "message_id": message_id,
                    "data": result.data,
                    "template_name": template_name,
                    "phone_number": phone_number
                }
            else:
                logger.error(f"❌ OFFICIAL TEMPLATE FAILED: {result.error_message}")
                return {
                    "success": False,
                    "error": result.error_message or "Failed to send official template message"
                }
                
        except Exception as e:
            logger.error(f"❌ OFFICIAL TEMPLATE ERROR: {str(e)}")
            return {
                "success": False,
                "error": f"Template messaging error: {str(e)}"
            }
    
    def _build_template_components(
        self,
        header_params: Optional[List[str]] = None,
        body_params: Optional[List[str]] = None,
        button_params: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Build template components for Meta API
        """
        components = []
        
        # Header component (if parameters provided)
        if header_params:
            header_component = {
                "type": "header",
                "parameters": []
            }
            for param in header_params:
                header_component["parameters"].append({
                    "type": "text",
                    "text": param
                })
            components.append(header_component)
        
        # Body component (if parameters provided)
        if body_params:
            body_component = {
                "type": "body",
                "parameters": []
            }
            for param in body_params:
                body_component["parameters"].append({
                    "type": "text",
                    "text": param
                })
            components.append(body_component)
        
        # Button component (if parameters provided)
        if button_params:
            button_component = {
                "type": "button",
                "parameters": []
            }
            for button_type, button_value in button_params.items():
                button_component["parameters"].append({
                    "type": "button",
                    "sub_type": button_type,
                    "index": "0",
                    "parameters": [{
                        "type": "text",
                        "text": button_value
                    }]
                })
            components.append(button_component)
        
        return {"components": components}
    
    async def get_user_templates(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get available templates for user
        """
        try:
            templates = self.official_config_service.get_templates(user_id)
            # Filter only APPROVED templates
            approved_templates = [
                {
                    "id": template.id,
                    "template_name": template.template_name,
                    "category": template.category,
                    "language": template.language,
                    "status": template.template_status,
                    "content": template.content
                }
                for template in templates
                if template.template_status and template.template_status.upper() == "APPROVED"
            ]
            logger.info(f"Found {len(approved_templates)} approved templates out of {len(templates)} total templates for user {user_id}")
            return approved_templates
        except Exception as e:
            logger.error(f"Failed to get user templates: {e}")
            return []
    
    def get_official_devices(self, user_id: str) -> List[Device]:
        """
        Get ONLY Official WhatsApp API Active devices for user
        
        This is the SINGLE SOURCE for device filtering across the entire application.
        """
        try:
            # Get all user devices
            devices = self.db.query(Device).filter(
                Device.busi_user_id == user_id
            ).all()
            
            # Filter for Official API Active devices only
            official_devices = []
            for device in devices:
                # Check if device is marked as official and active
                if hasattr(device, 'is_official') and device.is_official:
                    if hasattr(device, 'meta_status') and device.meta_status == "ACTIVE":
                        official_devices.append(device)
                # Fallback: Check device name or other indicators
                elif "official" in device.device_name.lower() or "meta" in device.device_name.lower():
                    if device.session_status == "connected":
                        official_devices.append(device)
            
            logger.info(f"Found {len(official_devices)} official devices for user {user_id}")
            return official_devices
            
        except Exception as e:
            logger.error(f"Failed to get official devices for user {user_id}: {e}")
            return []

# Global functions for easy access (used by existing code)
async def send_official_text_message(
    db: Session,
    user_id: str,
    phone_number: str,
    message_text: str,
    device_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    ✅ Send official WhatsApp text message
    
    This is the main function that should be called for official text messaging.
    """
    service = OfficialMessageService(db)
    return await service.send_official_text_message(
        user_id=user_id,
        phone_number=phone_number,
        message_text=message_text,
        device_id=device_id
    )

async def send_official_template_message(
    db: Session,
    user_id: str,
    phone_number: str,
    template_name: str,
    language_code: str = "en_US",
    header_params: Optional[List[str]] = None,
    body_params: Optional[List[str]] = None,
    button_params: Optional[Dict[str, str]] = None,
    device_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    ✅ Send official WhatsApp template message
    
    This is the main function that should be called for official template messaging.
    """
    service = OfficialMessageService(db)
    return await service.send_official_template_message(
        user_id=user_id,
        phone_number=phone_number,
        template_name=template_name,
        language_code=language_code,
        header_params=header_params,
        body_params=body_params,
        button_params=button_params,
        device_id=device_id
    )

def get_official_devices(db: Session, user_id: str) -> List[Device]:
    """
    Get Official WhatsApp API Active devices only
    
    This replaces all device filtering logic across the application.
    """
    service = OfficialMessageService(db)
    return service.get_official_devices(user_id)
