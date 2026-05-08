import asyncio
import logging
import requests
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, text
from models.google_sheet import GoogleSheet, GoogleSheetTrigger, GoogleSheetTriggerHistory, SheetStatus, TriggerType, TriggerHistoryStatus
from models.device import Device
from services.google_sheets_service import GoogleSheetsService
from services.unified_whatsapp_sender import send_whatsapp_message
from services.google_sheets_official_messaging import GoogleSheetsOfficialMessagingService
from services.whatsapp_engine_service import WhatsAppEngineService

logger = logging.getLogger(__name__)

class GoogleSheetsAutomationService:
    def __init__(self, db: Session):
        self.db = db
        self.sheets_service = GoogleSheetsService()
        self.official_messaging_service = GoogleSheetsOfficialMessagingService(db)
        # self.whatsapp_service removed in favor of direct unified_whatsapp_sender usage
        self.engine_service = WhatsAppEngineService(db)
    
    async def check_device_health(self, device_id: uuid.UUID) -> bool:
        """Check if device is healthy before processing triggers"""
        try:
            device_status = self.engine_service.check_device_status(str(device_id))
            return device_status.get("status") == "connected"
        except Exception as e:
            logger.error(f"Error checking device health for {device_id}: {e}")
            return False
    
    async def process_all_active_triggers(self):
        """Process all active triggers for all sheets"""
        try:
            # Check if google_sheets table exists
            try:
                # Test if table exists by running a simple query
                self.db.execute(text("SELECT 1 FROM google_sheets LIMIT 1"))
            except Exception as table_error:
                logger.info(f"Google Sheets tables not found - skipping trigger processing: {str(table_error)}")
                return
            
            # Get all active sheets
            active_sheets = self.db.query(GoogleSheet).filter(
                GoogleSheet.status == SheetStatus.ACTIVE
            ).all()
            
            if not active_sheets:
                logger.debug("No active sheets found for trigger processing")
                return
            
            logger.info(f"Processing triggers for {len(active_sheets)} active sheets")
            
            # Track device health status to avoid repetitive logging
            unhealthy_devices = set()
            orphaned_devices = set()
            
            for sheet in active_sheets:
                await self.process_sheet_triggers(sheet, unhealthy_devices, orphaned_devices)
                
        except Exception as e:
            logger.error(f"Error processing all active triggers: {e}")
            try:
                self.db.rollback()  # 🔧 CRITICAL: Rollback to prevent transaction issues
            except Exception as rollback_error:
                logger.error(f"Failed to rollback transaction: {rollback_error}")
    
    async def process_sheet_triggers(self, sheet: GoogleSheet, unhealthy_devices: set = None, orphaned_devices: set = None):
        """Process all triggers for a specific sheet"""
        if unhealthy_devices is None:
            unhealthy_devices = set()
        if orphaned_devices is None:
            orphaned_devices = set()
            
        try:
            # Get active triggers for this sheet
            triggers = self.db.query(GoogleSheetTrigger).filter(
                and_(
                    GoogleSheetTrigger.sheet_id == sheet.id,  # Use sheet.id
                    GoogleSheetTrigger.is_enabled == True
                )
            ).all()
            
            if not triggers:
                logger.debug(f"No active triggers found for sheet {sheet.spreadsheet_id}")
                return
            
            logger.debug(f"Processing {len(triggers)} triggers for sheet {sheet.spreadsheet_id}")
            
            # TODO: Get OAuth token for the sheet owner
            # For now, we'll skip actual API calls
            
            processed_count = 0
            skipped_count = 0
            disabled_count = 0
            
            for trigger in triggers:
                try:
                    # 🔧 CRITICAL: Handle UndefinedColumn errors gracefully
                    # Access trigger attributes safely to prevent column errors
                    try:
                        # Test access to last_processed_row to catch schema errors early
                        _ = trigger.last_processed_row
                    except Exception as attr_error:
                        if "last_processed_row" in str(attr_error):
                            logger.error(f"Schema error: last_processed_row column missing. Skipping trigger {trigger.trigger_id}")
                            skipped_count += 1
                            continue
                        else:
                            # Re-raise if it's a different attribute error
                            raise attr_error
                    
                    # Validate device_id format before processing
                    if not self._is_valid_device_id(trigger.device_id):
                        logger.warning(f"Skipping trigger {trigger.trigger_id} - invalid device_id format: {trigger.device_id}")
                        skipped_count += 1
                        continue
                    
                    # Check device status explicitly
                    # This replaces the confusing _check_device_health + _get_device_health_reason pattern
                    # to avoid race conditions and misleading logs.
                    
                    device_status_resp = self.engine_service.check_device_status(str(trigger.device_id))
                    status = device_status_resp.get("status", "unknown")
                    
                    if status == "connected":
                        # Device is healthy and ready
                        # Proceed to process trigger
                        pass 
                        
                    elif status == "connecting":
                        # Warm-up state - Skip silently or with info, but don't mark as error
                        if trigger.device_id not in unhealthy_devices:
                            logger.info(f"Device {trigger.device_id} is warming up (connecting). Skipping trigger cycle.")
                            unhealthy_devices.add(trigger.device_id)
                        skipped_count += 1
                        continue
                        
                    else:
                        # Device is truly unhealthy (disconnected, qr_ready, not_found, etc)
                        if trigger.device_id not in unhealthy_devices:
                            health_reason = device_status_resp.get("error") or f"Device status is '{status}'"
                            
                            # Log appropriate level
                            if status in ["disconnected", "qr_ready", "not_found"]:
                                logger.warning(f"Device {trigger.device_id} unavailable: {health_reason}. Skipping triggers.")
                            else:
                                logger.error(f"Device {trigger.device_id} error: {health_reason}")
                                
                            unhealthy_devices.add(trigger.device_id)
                            
                        # Handle orphaned triggers if needed (optional logic from before)
                        if status == "not_found" and trigger.device_id not in orphaned_devices:
                             # Logic to disable orphaned triggers if desired
                             pass
                             
                        skipped_count += 1
                        continue
                    
                    await self.process_single_trigger(sheet, trigger)
                    processed_count += 1
                    
                except Exception as e:
                    # 🔧 CRITICAL: Catch UndefinedColumn errors specifically
                    error_str = str(e).lower()
                    if "undefinedcolumn" in error_str or "column" in error_str and "does not exist" in error_str:
                        logger.error(f"Schema error in trigger {trigger.trigger_id}: {e}. Skipping this trigger.")
                        skipped_count += 1
                        continue
                    else:
                        logger.error(f"Error processing trigger {trigger.trigger_id}: {e}")
                        skipped_count += 1
                        # Continue processing other triggers
                        continue
            
            # Log summary only if there's activity
            if processed_count > 0 or skipped_count > 0 or disabled_count > 0:
                logger.info(f"Sheet {sheet.spreadsheet_id}: {processed_count} processed, {skipped_count} skipped, {disabled_count} disabled")
                
        except Exception as e:
            logger.error(f"Error processing triggers for sheet {sheet.spreadsheet_id}: {e}")
            try:
                self.db.rollback()  # 🔧 CRITICAL: Rollback to prevent transaction issues
            except Exception as rollback_error:
                logger.error(f"Failed to rollback transaction: {rollback_error}")
    
    def _is_valid_device_id(self, device_id) -> bool:
        """Check if device_id is a valid UUID format"""
        if not device_id:
            return False
        
        try:
            str(device_id)
            return True
        except (ValueError, AttributeError):
            return False
    
    async def _check_device_health(self, device_id: str) -> bool:
        """Check if device is healthy"""
        try:
            # Replaced legacy UnifiedWhatsAppService with engine_service
            device_status = self.engine_service.check_device_status(str(device_id))
            return device_status.get("status") == "connected"
        except Exception as e:
            logger.error(f"Error checking device health for {device_id}: {e}")
            return False
    
    async def _get_device_health_reason(self, device_id: str) -> str:
        """Get detailed reason for device being unhealthy"""
        try:
            # Check engine health first
            engine_health = self.engine_service.check_engine_health()
            if not engine_health["healthy"]:
                return f"WhatsApp Engine unhealthy: {engine_health.get('error', 'Unknown error')}"
            
            # Check device status
            device_status = self.engine_service.check_device_status(str(device_id))
            status = device_status.get("status", "unknown")
            
            if status == "connected":
                return "Device is connected and healthy"
            elif status == "not_found":
                return "Device missing from WhatsApp Engine (may need reconnection)"
            elif status == "disconnected":
                return "Device session is disconnected"
            elif status == "qr_ready":
                return "Device session is pending QR scan"
            elif status == "connecting":
                return "Device is currently connecting"
            elif status == "engine_unreachable":
                return "WhatsApp Engine is not reachable"
            else:
                return f"Device status is '{status}'"
                
        except Exception as e:
            logger.error(f"Health check failed for device {device_id}: {e}")
            return f"Health check failed: {str(e)}"
    
    async def process_single_trigger(self, sheet: GoogleSheet, trigger: GoogleSheetTrigger):
        """Process a single trigger using REAL Google Sheet data"""
        try:
            logger.info(f"🔍 Checking sheet '{sheet.sheet_name}' (ID: {sheet.spreadsheet_id}) for trigger conditions...")
            
            # Fetch real data using service account
            # Note: We use the server's service account, assuming generic access or share
            rows, headers = self.sheets_service.get_sheet_data_with_headers(
                credentials=None,
                spreadsheet_id=sheet.spreadsheet_id,
                worksheet_name=sheet.worksheet_name or "Sheet1"
            )
            
            if not rows:
                logger.debug(f"   No rows found in sheet {sheet.spreadsheet_id}")
                return

            # 🔥 FIX: Auto-detect status column if missing (Status vs Sent)
            current_status_col = getattr(trigger, 'status_column', 'Status') or 'Status'
            
            # Helper to find header case-insensitive
            found_status_header = None
            if headers:
                for h in headers:
                    if h.strip().lower() == current_status_col.strip().lower():
                        found_status_header = h
                        break
                
                # If configured status not found, try "Sent" as fallback
                if not found_status_header:
                    for h in headers:
                        if h.strip().lower() == "sent":
                            found_status_header = h
                            logger.info(f"   Note: Configured status column '{current_status_col}' not found. Using '{h}' instead.")
                            # Update trigger object (in-memory only for this cycle)
                            trigger.status_column = h
                            break

            logger.info(f"   Fetched {len(rows)} rows. Scanning for '{getattr(trigger, 'status_column', 'Status')}' == '{trigger.trigger_value}'...")

            match_count = 0
            for row_info in rows:
                # Process each row
                # The process_row_for_trigger function handles the logic:
                # 1. Check if Status == Send
                # 2. Check if valid phone
                # 3. Send Message
                # 4. Update Status to Sent/Failed
                
                # We can optimize by peeking at status first to avoid function call overhead
                # but for robustness, we delegate to the helper.
                
                # A small optimization: checks handled inside.
                await self.process_row_for_trigger(sheet, trigger, row_info)
            
        except Exception as e:
            logger.error(f"Error processing trigger {trigger.trigger_id}: {e}")
    
    async def process_row_for_trigger(self, sheet: GoogleSheet, trigger: GoogleSheetTrigger, row_info: Dict[str, Any]):
        """
        🔥 STEP 3: FIX TRIGGER AUTOMATION STABILITY
        
        Fix google_sheets_automation service so:
        - It does NOT crash on missing columns
        - It safely skips invalid rows
        - It handles missing phone values gracefully
        
        Fix error:
        - "cannot access local variable 'phone'"
        """
        try:
            row_data = row_info['data']
            row_number = row_info['row_number']
            
            # Helper for case-insensitive lookup
            def get_value_ci(data: dict, key: str) -> str:
                if not key: return ""
                # Direct match first (fast)
                if key in data: return data[key]
                # Case-insensitive match (slow)
                k_lower = key.strip().lower()
                for k, v in data.items():
                    if k.strip().lower() == k_lower:
                        return v
                return ""

            # 🔥 FIX: Initialize variables to prevent "cannot access local variable" errors
            
            # 🔥 FIX: Initialize variables to prevent "cannot access local variable" errors
            phone = None
            validated_phone = None
            message = ""
            
            # 🔥 RULE 1: Check status matches trigger value (CASE INSENSITIVE)
            status_column = getattr(trigger, 'status_column', 'Status')  # Safe attribute access
            current_status = str(get_value_ci(row_data, status_column)).strip().lower()
            
            # Get configured trigger value (Default to "Send")
            target_value = str(getattr(trigger, 'trigger_value', 'Send') or 'Send').strip().lower()
            
            # Additional safety: if target is "send", also allow empty/pending if that was the old logic, 
            # BUT user explicitly asked for "Status === Send". So we stick to THAT.
            # However, to be safe, if the cell is completely empty, it's definitely not a "Send" command.
            
            if current_status != target_value:
                # logger.debug(f"Row {row_number}: Status '{current_status}' != '{target_value}' - skipping")
                return
            
            logger.info(f"🎯 Row {row_number}: MATCH! Status '{current_status}' == '{target_value}'")
            
            # 🔥 RULE 1.5: TIME BASED CHECK
            if trigger.trigger_type == "time":
                # Get schedule column from config or default to 'ScheduleTime'
                config = trigger.trigger_config or {}
                schedule_column = config.get('schedule_column', 'ScheduleTime')
                schedule_time_str = get_value_ci(row_data, schedule_column)

                if not schedule_time_str:
                    logger.debug(f"   Row {row_number}: Time trigger but no value in '{schedule_column}' - skipping")
                    return

                try:
                    # Clean the time string
                    schedule_time_str = str(schedule_time_str).strip()
                    
                    # Try parsing common formats
                    # 1. ISO format: 2024-01-30T15:00:00
                    # 2. Excel/Sheet format: 2024-01-30 15:00:00
                    # 3. Simple date: 2024-01-30
                    
                    from dateutil import parser
                    scheduled_time = parser.parse(schedule_time_str)
                    
                    # Ensure timezone awareness if needed, but for now compare naive/naive or aware/aware
                    # Using current server time (naive if not specified)
                    now = datetime.now()
                    
                    if scheduled_time > now:
                        # Future time, do not send yet
                        return
                        
                    logger.info(f"   ⏰ Time condition met: {scheduled_time} <= {now}")
                    
                except Exception as e:
                    logger.warning(f"   Row {row_number}: Failed to parse schedule time '{schedule_time_str}': {e} - skipping")
                    return
            
            # 🔥 FIX: Safe phone column access
            phone_column = getattr(trigger, 'phone_column', 'phone')  # Safe attribute access
            phone = get_value_ci(row_data, phone_column)
            
            if not phone:
                error_msg = f"No phone number found in column '{phone_column}'"
                logger.warning(f"   Row {row_number}: {error_msg}")
                
                await self.create_trigger_history(
                    sheet.id,
                    trigger.trigger_id,
                    trigger.device_id,
                    row_number,
                    '',
                    '',
                    TriggerHistoryStatus.FAILED,
                    error_msg
                )
                return
            
            # Validate phone number
            validated_phone = self.sheets_service.validate_phone_number(str(phone))
            if not validated_phone:
                error_msg = f"Invalid phone number format: {phone}"
                logger.warning(f"   Row {row_number}: {error_msg}")
                
                await self.create_trigger_history(
                    sheet.id,
                    trigger.trigger_id,
                    trigger.device_id,
                    row_number,
                    phone,
                    '',
                    TriggerHistoryStatus.FAILED,
                    error_msg
                )
                return
            
            # 🔥 FIX: Safe message template access
            message_template = getattr(trigger, 'message_template', 'Hello {name}')  # Safe with default
            
            # ✅ CHECK: Is this an official template trigger?
            trigger_config = getattr(trigger, 'trigger_config', {}) or {}
            is_official_template = trigger_config.get('template_type') == 'official'
            
            if is_official_template:
                # ✅ OFFICIAL TEMPLATE LOGIC
                logger.info(f"📋 Row {row_number}: Processing OFFICIAL TEMPLATE trigger")
                logger.info(f"   Template: {trigger_config.get('template_name')}")
                logger.info(f"   Language: {trigger_config.get('language_code')}")
                
                # Extract template configuration
                template_name = trigger_config.get('template_name')
                language_code = trigger_config.get('language_code', 'en_US')
                header_param_columns = trigger_config.get('header_param_columns', [])
                body_param_columns = trigger_config.get('body_param_columns', [])
                button_param_columns = trigger_config.get('button_param_columns', {})
                
                # Build message description for logging
                param_summary = []
                if header_param_columns:
                    param_summary.append(f"Header:{','.join(header_param_columns)}")
                if body_param_columns:
                    param_summary.append(f"Body:{','.join(body_param_columns)}")
                if button_param_columns:
                    param_summary.append(f"Buttons:{list(button_param_columns.keys())}")
                
                message = f"Official Template: {template_name} ({language_code}) - Params: {', '.join(param_summary) if param_summary else 'None'}"
                
            else:
                # ❌ OLD UNOFFICIAL LOGIC (deprecated)
                logger.warning(f"⚠️ Row {row_number}: Processing LEGACY unofficial trigger (should be migrated to official)")
                message = self.sheets_service.process_message_template(message_template, row_data)
            
            # 🔥 RULE 2: ONE ROW AT A TIME with status updates
            try:
                # Mark as SENDING first
                await self.update_sheet_row_status(sheet, row_number, status_column, "Sending")
                
                logger.info(f"📤 Processing row {row_number} - ONE AT A TIME")
                logger.info(f"   Device ID: {str(trigger.device_id)}")
                logger.info(f"   Phone: {validated_phone}")
                logger.info(f"   Message: {message[:100]}...")
                
                # Create PENDING history entry
                await self.create_trigger_history(
                    sheet.id,
                    trigger.trigger_id,
                    trigger.device_id,
                    row_number,
                    validated_phone,
                    message,
                    TriggerHistoryStatus.PENDING  # Mark as pending initially
                )
                
                # Send message asynchronously in background (non-blocking)
                # This will not wait for WhatsApp delivery confirmation
                asyncio.create_task(
                    self.send_message_async_background(
                        str(trigger.device_id), 
                        validated_phone, 
                        message,
                        sheet.id,
                        trigger.trigger_id,
                        row_number,
                        status_column,  # Pass status column for updates
                        is_official_template=is_official_template,
                        trigger_config=trigger_config if is_official_template else None,
                        row_data=row_data
                    )
                )
                
                # Update trigger's last processed row immediately
                trigger.last_processed_row = max(getattr(trigger, 'last_processed_row', 0), row_number)
                
                logger.info(f"✅ Row {row_number} queued for delivery (ONE AT A TIME)")
                
            except Exception as e:
                # Mark as FAILED immediately
                await self.update_sheet_row_status(sheet, row_number, status_column, "FAILED")
                
                logger.error(f"❌ Failed to process row {row_number}: {str(e)}")
                
                await self.create_trigger_history(
                    sheet.id,
                    trigger.trigger_id,
                    trigger.device_id,
                    row_number,
                    validated_phone or phone,
                    message,
                    TriggerHistoryStatus.FAILED,
                    str(e)
                )
        
        except Exception as e:
            logger.error(f"❌ Error processing row {row_number} for trigger {trigger.trigger_id}: {str(e)}")
            
            # 🔥 FIX: Safe variable access in error handling
            safe_phone = validated_phone if 'validated_phone' in locals() else (phone if 'phone' in locals() else '')
            safe_message = message if 'message' in locals() else ''
            
            await self.create_trigger_history(
                sheet.id,
                trigger.trigger_id,
                trigger.device_id,
                row_number,
                safe_phone,
                safe_message,
                TriggerHistoryStatus.FAILED,
                str(e)
            )
    
    async def update_sheet_row_status(self, sheet: GoogleSheet, row_number: int, status_column: str, status: str):
        """
        Update sheet row status - ONE ROW AT A TIME
        """
        try:
            # Use the newly implemented update_cell method
            success = self.sheets_service.update_cell(
                sheet.spreadsheet_id, 
                sheet.worksheet_name, 
                row_number, 
                status_column, 
                status
            )
            
            if success:
                logger.info(f"📝 Updated row {row_number} status to '{status}' in column '{status_column}'")
            else:
                logger.warning(f"Failed to update row {row_number} status to '{status}' (API call failed)")
            
        except Exception as e:
            logger.error(f"Failed to update sheet row status: {e}")
    
    async def send_message_async_background(self, device_id: str, phone: str, message: str, 
                                          sheet_id: uuid.UUID, trigger_id: uuid.UUID, row_number: int, 
                                          status_column: str = 'status', is_official_template: bool = False,
                                          trigger_config: Dict[str, Any] = None, row_data: Dict[str, Any] = None):
        """
        ✅ Send message in background using OFFICIAL TEMPLATE or UNIFIED SENDER
        
        Args:
            device_id: Device ID (kept for compatibility)
            phone: Phone number
            message: Message content (for unofficial) or description (for official)
            sheet_id: Sheet ID
            trigger_id: Trigger ID
            row_number: Row number
            status_column: Status column name
            is_official_template: Whether to use official template messaging
            trigger_config: Trigger configuration for official templates
            row_data: Row data for official template parameter extraction
        """
        try:
            if is_official_template and trigger_config and row_data:
                # ✅ OFFICIAL TEMPLATE LOGIC
                logger.info(f"🔄 Background sending OFFICIAL TEMPLATE to {phone}...")
                
                # Extract template configuration
                template_name = trigger_config.get('template_name')
                language_code = trigger_config.get('language_code', 'en_US')
                header_param_columns = trigger_config.get('header_param_columns', [])
                body_param_columns = trigger_config.get('body_param_columns', [])
                button_param_columns = trigger_config.get('button_param_columns', {})
                
                # Get user_id from sheet
                sheet = self.db.query(GoogleSheet).filter(GoogleSheet.id == sheet_id).first()
                user_id = str(sheet.user_id) if sheet else None
                
                if not user_id:
                    raise Exception("User ID not found for official template sending")
                
                # Send official template message
                response = await self.official_messaging_service.send_sheet_row_official_message(
                    sheet=sheet,
                    device_id=device_id,  # Kept for compatibility
                    user_id=user_id,
                    row_data=row_data,
                    template_name=template_name,
                    language_code=language_code,
                    phone_column="phone",  # We already have the validated phone
                    header_param_columns=header_param_columns,
                    body_param_columns=body_param_columns,
                    button_param_columns=button_param_columns
                )
                
                logger.info(f"   Background Official Template Response: {response}")
                
            else:
                # ❌ OLD UNOFFICIAL LOGIC (deprecated)
                logger.warning(f"🔄 Background sending UNOFFICIAL message to {phone} (should migrate to official)...")
                
                # Use the unified WhatsApp sender (synchronous but robust)
                # We run it directly (blocking) to ensure reliability matches manual send
                response = send_whatsapp_message(device_id, phone, message)
                
                logger.info(f"   Background Unified Sender Response: {response}")
            
            if response and response.get("success"):
                # Update trigger history to SENT
                await self.update_trigger_history_status(
                    sheet_id,
                    trigger_id,
                    row_number,
                    phone,
                    TriggerHistoryStatus.SENT
                )
                
                # 🔥 RULE 2: Update sheet status to SENT
                try:
                    sheet = self.db.query(GoogleSheet).filter(GoogleSheet.id == sheet_id).first()
                    if sheet:
                        await self.update_sheet_row_status(sheet, row_number, status_column, "SENT")
                    else:
                        logger.error(f"Sheet {sheet_id} not found for status update")
                except Exception as e:
                    logger.error(f"Failed to update sheet status to SENT: {e}")
                
                send_type = "Official Template" if is_official_template else "Unofficial Message"
                logger.info(f"✅ Background {send_type} sent successfully to {phone}")
            else:
                error_msg = response.get("error", "Unknown error") if response else "No response from sender"
                logger.error(f"❌ Background message failed: {error_msg}")
                
                # Update trigger history to FAILED
                await self.update_trigger_history_status(
                    sheet_id,
                    trigger_id,
                    row_number,
                    phone,
                    TriggerHistoryStatus.FAILED,
                    error_msg
                )
                
                # 🔥 RULE 2: Update sheet status to FAILED
                try:
                    sheet = self.db.query(GoogleSheet).filter(GoogleSheet.id == sheet_id).first()
                    if sheet:
                        await self.update_sheet_row_status(sheet, row_number, status_column, "FAILED")
                except Exception as e:
                    logger.error(f"Failed to update sheet status to FAILED: {e}")
                
        except Exception as e:
            logger.error(f"❌ Background message sending exception: {str(e)}")
            
            # Update trigger history to FAILED
            await self.update_trigger_history_status(
                sheet_id,
                trigger_id,
                row_number,
                phone,
                TriggerHistoryStatus.FAILED,
                str(e)
            )
            
            # 🔥 RULE 2: Update sheet status to FAILED
            try:
                sheet = self.db.query(GoogleSheet).filter(GoogleSheet.id == sheet_id).first()
                if sheet:
                    await self.update_sheet_row_status(sheet, row_number, status_column, "FAILED")
            except Exception as e:
                logger.error(f"Failed to update sheet status to FAILED: {e}")
    
    async def update_trigger_history_status(self, sheet_id: uuid.UUID, trigger_id: uuid.UUID, 
                                          row_number: int, phone: str, status: TriggerHistoryStatus, 
                                          error_message: str = None):
        """Update existing trigger history status"""
        try:
            # Find the most recent PENDING entry for this trigger and row
            history = self.db.query(GoogleSheetTriggerHistory).filter(
                and_(
                    GoogleSheetTriggerHistory.sheet_id == sheet_id,
                    GoogleSheetTriggerHistory.trigger_id == trigger_id,
                    GoogleSheetTriggerHistory.row_number == row_number,
                    GoogleSheetTriggerHistory.status == TriggerHistoryStatus.PENDING
                )
            ).order_by(GoogleSheetTriggerHistory.created_at.desc()).first()
            
            if history:
                history.status = status
                history.error_message = error_message
                history.updated_at = datetime.utcnow()
                self.db.commit()
                logger.info(f"Updated trigger history status to {status} for row {row_number}")
            else:
                logger.warning(f"No pending trigger history found for update (sheet: {sheet_id}, trigger: {trigger_id}, row: {row_number})")
                
        except Exception as e:
            logger.error(f"Error updating trigger history status: {str(e)}")
            self.db.rollback()
    
    async def create_trigger_history(
        self,
        sheet_id: uuid.UUID,
        trigger_id: str,
        device_id: uuid.UUID,
        row_number: int,
        phone: str,
        message: str,
        status: TriggerHistoryStatus,
        error_message: Optional[str] = None
    ):
        """Create a trigger history record."""
        try:
            # Use correct table name and field names
            history = GoogleSheetTriggerHistory(
                sheet_id=sheet_id,
                device_id=device_id,
                phone_number=phone,  # Use phone_number, not phone
                message_content=message,  # Use message_content, not message
                status=status.value,
                error_message=error_message,
                triggered_at=datetime.utcnow()  # Use triggered_at, not executed_at
            )
            
            self.db.add(history)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error creating trigger history: {e}")
            self.db.rollback()
    
    def get_user_credentials(self, user_id: uuid.UUID):
        """Get OAuth credentials for a user"""
        # TODO: Implement OAuth token storage and retrieval
        # This would typically involve storing tokens in a secure way
        # and refreshing them when needed
        return None
    
    # Note: The polling loop is now handled by BackgroundTaskManager
    # This method is kept for backward compatibility but should not be used directly
    async def start_polling_loop(self, interval_seconds: int = 30):
        """
        DEPRECATED: Use BackgroundTaskManager.run_google_sheets_polling() instead.
        
        ⚠️ DANGEROUS: This method contains a blocking while loop and should NEVER be called
        from FastAPI startup events. It will block the entire application startup.
        
        This method is kept only for emergency manual testing and will block indefinitely.
        """
        logger.error("CRITICAL WARNING: start_polling_loop() contains blocking while loop!")
        logger.error("This method will block FastAPI startup and should NOT be used!")
        logger.error("Use BackgroundTaskManager.run_google_sheets_polling() instead.")
        
        # Add a safety check to prevent accidental blocking during startup
        import traceback
        logger.error(f"Call stack: {traceback.format_stack()[-3]}")
        
        # Continue with the blocking loop (only for manual testing)
        while True:
            try:
                await self.process_all_active_triggers()
                await asyncio.sleep(interval_seconds)
            except asyncio.CancelledError:
                logger.info("Google Sheets polling loop cancelled gracefully")
                break
            except Exception as e:
                logger.error(f"Error in polling loop: {e}")
                try:
                    await asyncio.sleep(10)
                except asyncio.CancelledError:
                    logger.info("Google Sheets polling loop cancelled during error recovery")
                    break

class TriggerProcessor:
    """Background task processor for Google Sheets triggers"""
    
    def __init__(self, db: Session):
        self.db = db
        self.automation_service = GoogleSheetsAutomationService(db)
    
    async def process_time_based_triggers(self):
        """Process time-based triggers"""
        try:
            # Get all time-based triggers that are due
            # This is a placeholder for time-based trigger logic
            current_time = datetime.utcnow()
            
            # TODO: Implement time-based trigger logic
            # This would involve checking trigger schedules and processing them
            
        except Exception as e:
            logger.error(f"Error processing time-based triggers: {e}")
    
    async def process_webhook_trigger(self, sheet_id: str, webhook_data: Dict[str, Any]):
        """Process a webhook-triggered event"""
        try:
            # Find the sheet
            sheet = self.db.query(GoogleSheet).filter(
                GoogleSheet.spreadsheet_id == sheet_id
            ).first()
            
            if not sheet:
                logger.warning(f"Webhook received for unknown sheet: {sheet_id}")
                return
            
            # Get active triggers for this sheet
            triggers = self.db.query(GoogleSheetTrigger).filter(
                and_(
                    GoogleSheetTrigger.sheet_id == sheet.id,  # Use sheet.id
                    GoogleSheetTrigger.is_enabled == True,
                    GoogleSheetTrigger.trigger_type.in_([TriggerType.NEW_ROW, TriggerType.UPDATE_ROW])
                )
            ).all()
            
            for trigger in triggers:
                await self.automation_service.process_single_trigger(sheet, trigger)
                
        except Exception as e:
            logger.error(f"Error processing webhook trigger: {e}")

# Global instance for background processing
automation_service = None

def get_automation_service(db: Session) -> GoogleSheetsAutomationService:
    """Get or create the automation service instance"""
    global automation_service
    if automation_service is None:
        automation_service = GoogleSheetsAutomationService(db)
    return automation_service
