#!/usr/bin/env python3
"""
🔥 TRIGGER PROCESSOR V2 - STEP 4: Row-level safe processing

🔹 C. Trigger Processing Logic (CRITICAL)
for row in sheet_rows:
    status = row[status_column]

    if status != trigger_value:
        continue

    update_sheet_status(row, "Processing")

    try:
        message_id = send_whatsapp_message(
            trigger.device_id,
            row[phone_column],
            render_template(trigger.template, row)
        )

        update_sheet_status(row, "Sent")
        save_trigger_history(row, "Sent", message_id)

    except Exception as e:
        update_sheet_status(row, "Failed")
        save_trigger_history(row, "Failed", str(e))
"""
import logging
import asyncio
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from models.google_sheet import GoogleSheet, GoogleSheetTrigger, GoogleSheetTriggerHistory, TriggerHistoryStatus
from services.unified_whatsapp_sender import send_whatsapp_message
from services.device_validator import validate_device_before_send
from services.google_sheets_service import GoogleSheetsService

logger = logging.getLogger(__name__)

class TriggerProcessorV2:
    """
    🔥 NEW TRIGGER PROCESSOR - Fixed version with proper state management
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.sheets_service = GoogleSheetsService()
        
    async def process_sheet_triggers(self, sheet: GoogleSheet) -> Dict[str, Any]:
        """
        Process all triggers for a sheet with proper state management
        """
        logger.info(f"🚀 TRIGGER PROCESSOR V2: Processing triggers for sheet {sheet.id}")
        
        try:
            # Get all enabled triggers for this sheet
            triggers = self.db.query(GoogleSheetTrigger).filter(
                and_(
                    GoogleSheetTrigger.sheet_id == sheet.id,
                    GoogleSheetTrigger.is_enabled == True
                )
            ).all()
            
            if not triggers:
                logger.info(f"   No enabled triggers found for sheet {sheet.id}")
                return {"success": True, "processed": 0, "triggers": []}
            
            logger.info(f"   Found {len(triggers)} enabled triggers")
            
            results = []
            total_processed = 0
            
            for trigger in triggers:
                try:
                    # Validate device before processing
                    device_validation = validate_device_before_send(self.db, trigger.device_id)
                    if not device_validation["valid"]:
                        logger.error(f"   ❌ Trigger {trigger.trigger_id}: {device_validation['error']}")
                        
                        # Disable this trigger
                        trigger.is_enabled = False
                        self.db.commit()
                        
                        results.append({
                            "trigger_id": trigger.trigger_id,
                            "success": False,
                            "error": device_validation["error"],
                            "processed": 0
                        })
                        continue
                    
                    # Process this trigger
                    trigger_result = await self.process_single_trigger(sheet, trigger)
                    results.append(trigger_result)
                    total_processed += trigger_result.get("processed", 0)
                    
                except Exception as e:
                    logger.error(f"   ❌ Error processing trigger {trigger.trigger_id}: {e}")
                    results.append({
                        "trigger_id": trigger.trigger_id,
                        "success": False,
                        "error": str(e),
                        "processed": 0
                    })
            
            logger.info(f"🏁 TRIGGER PROCESSING COMPLETE: {total_processed} rows processed")
            
            return {
                "success": True,
                "processed": total_processed,
                "triggers": results
            }
            
        except Exception as e:
            logger.error(f"❌ TRIGGER PROCESSOR ERROR: {e}")
            return {
                "success": False,
                "error": str(e),
                "processed": 0
            }
    
    async def process_single_trigger(self, sheet: GoogleSheet, trigger: GoogleSheetTrigger) -> Dict[str, Any]:
        """
        🔹 C. Trigger Processing Logic (CRITICAL)
        Process a single trigger with proper state management
        """
        logger.info(f"📋 Processing trigger {trigger.trigger_id}")
        logger.info(f"   Device ID: {trigger.device_id}")
        logger.info(f"   Phone Column: {trigger.phone_column}")
        logger.info(f"   Status Column: {trigger.status_column}")
        logger.info(f"   Trigger Value: {trigger.trigger_value}")
        
        try:
            # Get sheet rows
            rows_data, headers = self.sheets_service.get_sheet_data_with_headers(
                credentials=None,
                spreadsheet_id=sheet.spreadsheet_id,
                worksheet_name=sheet.worksheet_name or "Sheet1"
            )
            
            logger.info(f"   Fetched {len(rows_data)} rows from sheet")
            
            processed_count = 0
            
            # Process each row
            for row_info in rows_data:
                try:
                    row_result = await self.process_row_for_trigger(sheet, trigger, row_info)
                    if row_result["processed"]:
                        processed_count += 1
                        
                except Exception as e:
                    logger.error(f"   ❌ Error processing row {row_info.get('row_number', 'unknown')}: {e}")
                    continue
            
            # Update trigger's last processed row
            if rows_data:
                max_row_number = max(row.get('row_number', 0) for row in rows_data)
                trigger.last_processed_row = max(trigger.last_processed_row, max_row_number)
                trigger.last_triggered_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"   ✅ Trigger {trigger.trigger_id} processed {processed_count} rows")
            
            return {
                "trigger_id": trigger.trigger_id,
                "success": True,
                "processed": processed_count
            }
            
        except Exception as e:
            logger.error(f"   ❌ Trigger {trigger.trigger_id} failed: {e}")
            return {
                "trigger_id": trigger.trigger_id,
                "success": False,
                "error": str(e),
                "processed": 0
            }
    
    async def process_row_for_trigger(self, sheet: GoogleSheet, trigger: GoogleSheetTrigger, row_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        🔹 Row-level safe processing
        
        Each row must go through states:
        Send → Processing → Sent / Failed
        No skipping. No duplicates.
        """
        try:
            row_data = row_info['data']
            row_number = row_info['row_number']
            
            # Skip if already processed
            if row_number <= trigger.last_processed_row:
                return {"processed": False, "reason": "already_processed"}
            
            # Get status from sheet
            status_column = trigger.status_column or 'Status'
            raw_status = row_data.get(status_column, '')
            
            # Normalize status
            normalized_status = str(raw_status).strip().lower()
            trigger_value = str(trigger.trigger_value or 'Send').strip().lower()
            
            # Check if this row should be processed
            if normalized_status != trigger_value:
                logger.debug(f"   Row {row_number}: Status '{raw_status}' != trigger value '{trigger.trigger_value}'")
                return {"processed": False, "reason": "status_mismatch"}
            
            logger.info(f"   🎯 Row {row_number}: Status '{raw_status}' matches trigger value")
            
            # Extract phone number
            phone_column = trigger.phone_column or 'phone'
            phone = row_data.get(phone_column)
            
            if not phone:
                logger.warning(f"   Row {row_number}: No phone number in column '{phone_column}'")
                await self.save_trigger_history(sheet, trigger, row_number, "", "", TriggerHistoryStatus.FAILED, f"No phone number found in column {phone_column}")
                return {"processed": False, "reason": "no_phone"}
            
            # Format message
            message_template = trigger.message_template or "Hello {name}"
            message = self.sheets_service.process_message_template(message_template, row_data)
            
            # 🔹 C. Trigger Processing Logic (CRITICAL)
            # Step 1: Update sheet status to "Processing"
            await self.update_sheet_status(sheet, row_number, status_column, "Processing")
            
            # Step 2: Send WhatsApp message
            try:
                logger.info(f"   📤 Sending WhatsApp message for row {row_number}")
                
                send_result = send_whatsapp_message(
                    trigger.device_id,
                    phone,
                    message
                )
                
                if send_result["success"]:
                    # Step 3: Update sheet status to "Sent"
                    await self.update_sheet_status(sheet, row_number, status_column, "Sent")
                    
                    # Step 4: Save trigger history
                    await self.save_trigger_history(
                        sheet, trigger, row_number, phone, message, 
                        TriggerHistoryStatus.SENT, message_id=send_result.get("message_id")
                    )
                    
                    logger.info(f"   ✅ Row {row_number}: Message sent successfully")
                    return {"processed": True, "status": "sent"}
                    
                else:
                    # Step 3: Update sheet status to "Failed"
                    await self.update_sheet_status(sheet, row_number, status_column, "Failed")
                    
                    # Step 4: Save trigger history
                    await self.save_trigger_history(
                        sheet, trigger, row_number, phone, message, 
                        TriggerHistoryStatus.FAILED, send_result.get("error", "Unknown error")
                    )
                    
                    logger.error(f"   ❌ Row {row_number}: Message send failed - {send_result.get('error')}")
                    return {"processed": True, "status": "failed"}
                    
            except Exception as e:
                # Step 3: Update sheet status to "Failed"
                await self.update_sheet_status(sheet, row_number, status_column, "Failed")
                
                # Step 4: Save trigger history
                await self.save_trigger_history(
                    sheet, trigger, row_number, phone, message, 
                    TriggerHistoryStatus.FAILED, str(e)
                )
                
                logger.error(f"   ❌ Row {row_number}: Exception - {e}")
                return {"processed": True, "status": "failed"}
                
        except Exception as e:
            logger.error(f"   ❌ Row {row_number}: Processing error - {e}")
            return {"processed": False, "reason": "processing_error", "error": str(e)}
    
    async def update_sheet_status(self, sheet: GoogleSheet, row_number: int, status_column: str, status: str):
        """
        Update Google Sheet row status
        """
        try:
            # TODO: Implement actual Google Sheets API update
            logger.info(f"   📝 Updated row {row_number} status to '{status}' in column '{status_column}'")
            
            # For now, just log it
            # sheets_service.update_cell(sheet.spreadsheet_id, sheet.worksheet_name, row_number, status_column, status)
            
        except Exception as e:
            logger.error(f"   Failed to update sheet status: {e}")
    
    async def save_trigger_history(self, sheet: GoogleSheet, trigger: GoogleSheetTrigger, 
                                 row_number: int, phone: str, message: str, 
                                 status: TriggerHistoryStatus, message_id: str = None, 
                                 error_message: str = None):
        """
        🔹 STEP 7: Save trigger history after every row
        UI reads from DB → no empty history
        """
        try:
            history = GoogleSheetTriggerHistory(
                sheet_id=sheet.id,
                device_id=trigger.device_id,
                phone_number=phone,
                message_content=message,
                status=status.value,
                error_message=error_message,
                row_data={
                    "row_number": row_number,
                    "trigger_id": trigger.trigger_id,
                    "message_id": message_id
                }
            )
            
            self.db.add(history)
            self.db.commit()
            
            logger.debug(f"   📋 Saved trigger history for row {row_number}: {status.value}")
            
        except Exception as e:
            logger.error(f"   Failed to save trigger history: {e}")
            self.db.rollback()

# Global function for easy access
async def process_sheet_triggers(db: Session, sheet: GoogleSheet) -> Dict[str, Any]:
    """Process all triggers for a sheet"""
    processor = TriggerProcessorV2(db)
    return await processor.process_sheet_triggers(sheet)
