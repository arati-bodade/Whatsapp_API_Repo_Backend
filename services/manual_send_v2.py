#!/usr/bin/env python3
"""
🔥 MANUAL SEND V2 - STEP 5: Fix manual send to use unified logic

🔹 B. Manual Sheet Send Logic
for row in selected_rows:
    try:

✅ ONLY use official template functions:
- send_template_message() from OfficialWhatsAppConfigService

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

class ManualSendV2:
    """
    🔥 OFFICIAL WHATSAPP MANUAL SEND FOR GOOGLE SHEETS
    
    Handles sending official template messages only via Meta API
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.sheets_service = GoogleSheetsService()
        self.official_service = OfficialWhatsAppConfigService(db)
    
    async def send_manual_messages(
        self,
        sheet: GoogleSheet,
        device_id: str,  # Kept for compatibility, but not used in official messaging
        template_name: str,
        language_code: str = "en_US",
        phone_column: str = "phone",
        header_param_columns: Optional[List[str]] = None,
        body_param_columns: Optional[List[str]] = None,
        button_param_columns: Optional[Dict[str, str]] = None,
        selected_rows: Optional[List[Dict[str, Any]]] = None,
        send_all: bool = False
    ) -> Dict[str, Any]:
        """
        ✅ Send OFFICIAL WhatsApp template messages to Google Sheet recipients
        
        Args:
            sheet: Google Sheet object
            device_id: Device ID (kept for compatibility)
            template_name: Name of approved template
            language_code: Template language code
            phone_column: Column name containing phone numbers
            header_param_columns: List of column names for header parameters
            body_param_columns: List of column names for body parameters
            button_param_columns: Dict of {button_type: column_name} for button parameters
            selected_rows: Specific rows to send to (optional)
            send_all: Send to all rows (optional)
            
        Returns:
            Dict with send results including wamid message IDs
        """
        try:
            logger.info(f"🚀 OFFICIAL TEMPLATE MANUAL SEND: Starting")
            logger.info(f"   Sheet: {sheet.sheet_name}")
            logger.info(f"   Template: {template_name}")
            logger.info(f"   Language: {language_code}")
            logger.info(f"   User ID: {sheet.user_id}")
            
            # Get sheet data
            if send_all:
                rows_data, headers = self.sheets_service.get_sheet_data_with_headers(
                    credentials=None,
                    spreadsheet_id=sheet.spreadsheet_id,
                    worksheet_name=sheet.worksheet_name or "Sheet1"
                )
                logger.info(f"   Fetched {len(rows_data)} rows for send_all")
            elif selected_rows:
                rows_data = selected_rows
                logger.info(f"   Using {len(selected_rows)} selected rows")
            else:
                logger.warning("   No rows specified for sending")
                return {
                    "success": False,
                    "sent": 0,
                    "failed": 0,
                    "errors": ["No rows specified for sending"]
                }
            
            if not rows_data:
                logger.warning("   No rows to process")
                return {
                    "success": False,
                    "sent": 0,
                    "failed": 0,
                    "errors": ["No rows to process"]
                }
            
            # Process each row with official template messaging
            results = []
            errors = []
            success_count = 0
            failure_count = 0
            message_ids = []
            
            for i, row_data in enumerate(rows_data):
                row_number = i + 1
                try:
                    # Send official template message for this row
                    row_result = await self.send_official_template_to_row(
                        sheet=sheet,
                        user_id=str(sheet.user_id),
                        row_data=row_data,
                        row_number=row_number,
                        template_name=template_name,
                        language_code=language_code,
                        phone_column=phone_column,
                        header_param_columns=header_param_columns,
                        body_param_columns=body_param_columns,
                        button_param_columns=button_param_columns
                    )
                    
                    if row_result["success"]:
                        success_count += 1
                        if row_result.get("message_id"):
                            message_ids.append(row_result["message_id"])
                        logger.info(f"   ✅ Row {row_number}: Official template sent")
                    else:
                        failure_count += 1
                        error_msg = f"Row {row_number}: {row_result['error']}"
                        errors.append(error_msg)
                        logger.error(f"   ❌ Row {row_number}: {row_result['error']}")
                    
                    results.append(row_result)
                    
                except Exception as e:
                    failure_count += 1
                    error_msg = f"Row {row_number}: {str(e)}"
                    errors.append(error_msg)
                    logger.error(f"   ❌ Row {row_number}: Exception - {e}")
            
            total_count = success_count + failure_count
            
            logger.info(f"🏁 OFFICIAL TEMPLATE MANUAL SEND COMPLETE: {success_count} sent, {failure_count} failed")
            
            return {
                "success": success_count > 0,
                "sent": success_count,
                "failed": failure_count,
                "total": total_count,
                "errors": errors,
                "message_ids": message_ids
            }
            
        except Exception as e:
            logger.error(f"❌ OFFICIAL TEMPLATE MANUAL SEND ERROR: {str(e)}")
            return {
                "success": False,
                "sent": 0,
                "failed": 0,
                "errors": [f"Manual send error: {str(e)}"]
            }
    
    async def send_official_template_to_row(
        self,
        sheet: GoogleSheet,
        user_id: str,
        row_data: Dict[str, Any],
        row_number: int,
        template_name: str,
        language_code: str = "en_US",
        phone_column: str = "phone",
        header_param_columns: Optional[List[str]] = None,
        body_param_columns: Optional[List[str]] = None,
        button_param_columns: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        ✅ Send official template message to a single row
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
            
            # Get user's official WhatsApp config
            config = self.official_service.get_config_by_user_id(user_id)
            if not config:
                return {
                    "success": False,
                    "error": "Official WhatsApp configuration not found"
                }
            
            if not config.is_active:
                return {
                    "success": False,
                    "error": "Official WhatsApp configuration is not active"
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
            
            # Build template components for Meta API
            template_data = self._build_template_components(
                header_params=header_params,
                body_params=body_params,
                button_params=button_params
            )
            
            # Send official template message via Meta API
            result = self.official_service.send_template_message(
                config=config,
                to_number=validated_phone,
                template_name=template_name,
                template_data=template_data,
                language_code=language_code
            )
            
            if result.success:
                message_id = result.data.get('messages', [{}])[0].get('id') if result.data else None
                
                # Save manual history
                await self.save_manual_history(
                    sheet=sheet,
                    device_id="",  # Not used in official messaging
                    row_number=row_number,
                    phone=validated_phone,
                    message=f"Official Template: {template_name}",
                    status=TriggerHistoryStatus.SENT,
                    message_id=message_id
                )
                
                return {
                    "success": True,
                    "message_id": message_id,
                    "template_name": template_name,
                    "phone_number": validated_phone
                }
            else:
                # Save failed history
                await self.save_manual_history(
                    sheet=sheet,
                    device_id="",
                    row_number=row_number,
                    phone=validated_phone,
                    message=f"Official Template: {template_name}",
                    status=TriggerHistoryStatus.FAILED,
                    error_message=result.error_message
                )
                
                return {
                    "success": False,
                    "error": result.error_message or "Failed to send official template message"
                }
                
        except Exception as e:
            logger.error(f"❌ ROW OFFICIAL TEMPLATE ERROR: {str(e)}")
            return {
                "success": False,
                "error": f"Row processing error: {str(e)}"
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
    
    async def save_manual_history(self, sheet: GoogleSheet, device_id: str,
                                row_number: int, phone: str, message: str,
                                status: TriggerHistoryStatus, message_id: str = None,
                                error_message: str = None):
        """
        Save manual send history
        """
        try:
            history = GoogleSheetTriggerHistory(
                sheet_id=sheet.id,
                device_id=device_id,
                phone_number=phone,
                message_content=message,
                status=status.value,
                error_message=error_message,
                row_data={
                    "row_number": row_number,
                    "send_type": "manual_official_template",
                    "message_id": message_id
                }
            )
            
            self.db.add(history)
            self.db.commit()
            
            logger.debug(f"   📋 Saved manual history for row {row_number}: {status.value}")
            
        except Exception as e:
            logger.error(f"   Failed to save manual history: {e}")
            self.db.rollback()

# Global function for easy access
async def send_manual_messages(db: Session, sheet: GoogleSheet, device_id: str,
                             template_name: str, language_code: str = "en_US",
                             phone_column: str = "phone",
                             header_param_columns: Optional[List[str]] = None,
                             body_param_columns: Optional[List[str]] = None,
                             button_param_columns: Optional[Dict[str, str]] = None,
                             selected_rows: List[Dict[str, Any]] = None,
                             send_all: bool = False) -> Dict[str, Any]:
    """
    ✅ Send official WhatsApp template messages for Google Sheets integration
    
    This is the main function that should be called instead of unofficial messaging functions.
    """
    sender = ManualSendV2(db)
    return await sender.send_manual_messages(
        sheet, device_id, template_name, language_code, phone_column,
        header_param_columns, body_param_columns, button_param_columns,
        selected_rows, send_all
    )
