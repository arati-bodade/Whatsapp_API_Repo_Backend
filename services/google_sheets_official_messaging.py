#!/usr/bin/env python3
"""
🔥 GOOGLE SHEETS OFFICIAL MESSAGING SERVICE

This service handles ONLY OFFICIAL WhatsApp template messages for Google Sheets integration.
Replaces unofficial text messaging with official template-based messaging via Meta API.

✅ ONLY use official template functions:
- sendOfficialTemplateMessage()
- sendWhatsAppTemplate()  
- sendMetaOfficialMessage()

❌ NEVER call:
- sendUnofficialMessage()
- sendTextMessage()
- sendNormalMessage()
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from models.google_sheet import GoogleSheet, GoogleSheetTriggerHistory, TriggerHistoryStatus
from models.official_whatsapp_config import OfficialWhatsAppConfig
from services.official_whatsapp_config_service import OfficialWhatsAppConfigService
from services.google_sheets_service import GoogleSheetsService

logger = logging.getLogger(__name__)

class GoogleSheetsOfficialMessagingService:
    """
    🔥 OFFICIAL WHATSAPP MESSAGING FOR GOOGLE SHEETS
    
    Handles sending official template messages only via Meta API
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.sheets_service = GoogleSheetsService()
        self.official_service = OfficialWhatsAppConfigService(db)
    
    async def send_official_template_message(
        self,
        user_id: str,
        phone_number: str,
        template_name: str,
        language_code: str = "en_US",
        header_params: Optional[List[str]] = None,
        body_params: Optional[List[str]] = None,
        button_params: Optional[Dict[str, str]] = None
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
            
        Returns:
            Dict with success status and Meta API response (includes wamid)
        """
        try:
            logger.info(f"🚀 OFFICIAL TEMPLATE SEND: {template_name} to {phone_number}")
            
            # Standardize phone number format
            from utils.phone_utils import normalize_phone
            normalized_phone = normalize_phone(phone_number)
            if not normalized_phone:
                return {"success": False, "error": f"Invalid recipient number: {phone_number}"}
            phone_number = normalized_phone
            
            # Step 1: Get user's official WhatsApp config
            config = self.official_service.get_config_by_user_id(user_id)
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
            
            # Step 2: Build template components for Meta API
            template_data = self._build_template_components(
                header_params=header_params,
                body_params=body_params,
                button_params=button_params
            )
            
            # Step 3: Send via Meta API (official only)
            result = self.official_service.send_template_message(
                config=config,
                to_number=phone_number,
                template_name=template_name,
                template_data=template_data,
                language_code=language_code
            )
            
            if result.success:
                logger.info(f"✅ OFFICIAL TEMPLATE SENT: wamid={result.data.get('messages', [{}])[0].get('id')}")
                return {
                    "success": True,
                    "message_id": result.data.get('messages', [{}])[0].get('id'),
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
                    "index": "0",  # You may need to adjust this based on button order
                    "parameters": [{
                        "type": "text",
                        "text": button_value
                    }]
                })
            components.append(button_component)
        
        return {"components": components}
    
    async def send_sheet_row_official_message(
        self,
        sheet: GoogleSheet,
        device_id: str,  # Kept for compatibility, but not used in official messaging
        user_id: str,
        row_data: Dict[str, Any],
        template_name: str,
        language_code: str = "en_US",
        phone_column: str = "phone",
        header_param_columns: Optional[List[str]] = None,
        body_param_columns: Optional[List[str]] = None,
        button_param_columns: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        ✅ Send official template message for a Google Sheet row
        
        Maps sheet columns to template parameters and sends official message
        
        Args:
            sheet: Google Sheet object
            device_id: Device ID (kept for compatibility)
            user_id: Business user ID
            row_data: Row data from Google Sheet
            template_name: Template name to use
            language_code: Template language code
            phone_column: Column name containing phone numbers
            header_param_columns: List of column names for header parameters
            body_param_columns: List of column names for body parameters
            button_param_columns: Dict of {button_type: column_name} for button parameters
            
        Returns:
            Dict with send result
        """
        try:
            # Extract phone number
            phone = row_data.get(phone_column)
            if not phone:
                return {
                    "success": False,
                    "error": f"No phone number found in column '{phone_column}'"
                }
            
            # Validate and format phone number
            validated_phone = self.sheets_service.validate_phone_number(str(phone))
            if not validated_phone:
                return {
                    "success": False,
                    "error": f"Invalid phone number format: {phone}"
                }
            
            # Extract header parameters from sheet columns
            header_params = []
            if header_param_columns:
                for col in header_param_columns:
                    value = row_data.get(col, "")
                    header_params.append(str(value) if value else "")
            
            # Extract body parameters from sheet columns
            body_params = []
            if body_param_columns:
                for col in body_param_columns:
                    value = row_data.get(col, "")
                    body_params.append(str(value) if value else "")
            
            # Extract button parameters from sheet columns
            button_params = {}
            if button_param_columns:
                for button_type, col in button_param_columns.items():
                    value = row_data.get(col, "")
                    if value:
                        button_params[button_type] = str(value)
            
            # Send official template message
            result = await self.send_official_template_message(
                user_id=user_id,
                phone_number=validated_phone,
                template_name=template_name,
                language_code=language_code,
                header_params=header_params if header_params else None,
                body_params=body_params if body_params else None,
                button_params=button_params if button_params else None
            )
            
            return result
            
        except Exception as e:
            logger.error(f"❌ SHEET ROW OFFICIAL MESSAGE ERROR: {str(e)}")
            return {
                "success": False,
                "error": f"Row processing error: {str(e)}"
            }
    
    async def get_user_templates(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get available templates for user
        """
        try:
            templates = self.official_service.get_templates(user_id)
            return [
                {
                    "id": template.id,
                    "template_name": template.template_name,
                    "category": template.category,
                    "language": template.language,
                    "status": template.template_status,
                    "content": template.content
                }
                for template in templates
            ]
        except Exception as e:
            logger.error(f"Failed to get user templates: {e}")
            return []

# Global function for easy access
async def send_google_sheet_official_message(
    db: Session,
    user_id: str,
    phone_number: str,
    template_name: str,
    language_code: str = "en_US",
    header_params: Optional[List[str]] = None,
    body_params: Optional[List[str]] = None,
    button_params: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    ✅ Send official WhatsApp template message for Google Sheets integration
    
    This is the main function that should be called instead of unofficial messaging functions.
    """
    service = GoogleSheetsOfficialMessagingService(db)
    return await service.send_official_template_message(
        user_id=user_id,
        phone_number=phone_number,
        template_name=template_name,
        language_code=language_code,
        header_params=header_params,
        body_params=body_params,
        button_params=button_params
    )
