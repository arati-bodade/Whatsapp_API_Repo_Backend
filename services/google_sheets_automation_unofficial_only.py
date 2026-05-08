#!/usr/bin/env python3
"""
🔥 GOOGLE SHEETS AUTOMATION SERVICE - UNOFFICIAL WHATSAPP API ONLY

This service handles Google Sheet triggers using ONLY Unofficial WhatsApp API.
Completely removes all official WhatsApp logic and uses device-based messaging only.

✅ FEATURES:
- Process triggers using Unofficial WhatsApp devices only
- Send messages via WhatsApp Engine (unofficial)
- Device validation and health checks
- Proper error handling and logging

❌ REMOVED:
- All official WhatsApp API logic
- OfficialWhatsAppConfig dependencies
- OfficialMessageService dependencies
- Template-based messaging logic
"""

import asyncio
import logging
import uuid
import re
import os
import pandas as pd
from datetime import datetime, timedelta, timezone, time, date
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, text

from models.google_sheet import GoogleSheet, GoogleSheetTrigger, GoogleSheetTriggerHistory, SheetStatus, TriggerType, TriggerHistoryStatus
from models.device import Device
from services.google_sheets_service import GoogleSheetsService
from services.unified_service import UnifiedWhatsAppService
from schemas.unified import UnifiedMessageRequest, MessageType
from services.device_validator import validate_device_before_send

# 🔥 STATUS NORMALIZATION CONSTANTS
VALID_TRIGGER_STATUSES = {
    "scheduled": "SCHEDULED",
    "send": "SEND", 
    "sent": "SENT",
    "sending": "SENDING",
    "failed": "FAILED"
}

logger = logging.getLogger(__name__)

class GoogleSheetsAutomationServiceUnofficial:
    """
    🔥 UNOFFICIAL WHATSAPP GOOGLE SHEETS AUTOMATION
    
    Processes Google Sheet triggers using ONLY Unofficial WhatsApp API
    """
    
    # 🔥 IN-MEMORY ROW LOCKING
    # Tracks (sheet_id, row_number) combinations currently being processed
    _processing_rows = set()
    
    def __init__(self, db: Session):
        self.db = db
        self.sheets_service = GoogleSheetsService()
        self.unified_service = UnifiedWhatsAppService(db)

    def _load_local_file_data(self, file_path: str) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        🚀 Load data from a local CSV or Excel file.
        Returns (rows_data, headers_data) in the same format as GoogleSheetsService.
        """
        logger.info(f"📁 Loading local file data: {file_path}")
        
        # Normalize path separators
        file_path = file_path.replace("\\", "/")
        
        # Check if already absolute and exists
        if os.path.isabs(file_path) and os.path.exists(file_path):
            pass
        elif not os.path.exists(file_path):
            # Try prepending current directory or common upload paths
            base_dir = os.getcwd()
            base_paths = [
                base_dir,
                os.path.join(base_dir, "uploads"),
                os.path.join(base_dir, "uploads/campaign_data"),
                os.path.join(base_dir, "uploads/trigger_media")
            ]
            found = False
            
            # Extract basename if it's a messed up path
            basename = os.path.basename(file_path)
            
            for bp in base_paths:
                # Try with full path first
                test_path = os.path.join(bp, file_path) if not file_path.startswith("/") else file_path
                if os.path.exists(test_path):
                    file_path = test_path
                    found = True
                    break
                # Try with just basename
                test_path_base = os.path.join(bp, basename)
                if os.path.exists(test_path_base):
                    file_path = test_path_base
                    found = True
                    break
            
            if not found:
                logger.error(f"❌ File not found: {file_path}")
                return [], []

        try:
            # Determine file type
            ext = os.path.splitext(file_path)[1].lower()
            
            if ext == '.csv':
                df = pd.read_csv(file_path)
            elif ext in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            else:
                logger.error(f"❌ Unsupported file type: {ext}")
                return [], []

            # Clean and format data
            df = df.where(pd.notnull(df), None) # Convert NaN to None
            
            # Ensure headers are strings and clean
            headers = [str(h).strip() for h in df.columns.tolist()]
            df.columns = headers
            
            rows_data = []
            for idx, row in df.iterrows():
                row_dict = row.to_dict()
                rows_data.append({
                    'data': row_dict,
                    'row_number': idx + 2 # Header is Row 1
                })
                
            return rows_data, headers
            
        except Exception as e:
            logger.error(f"❌ Failed to load file data: {e}")
            return [], []

    def get_case_insensitive_value(self, data: Dict[str, Any], key: Optional[str]) -> Any:
        """Helper to get value from dictionary with case-insensitive and stripped key matching"""
        if not key:
            return None
        
        # Normalize target key
        key_clean = key.strip().lower()
        
        # Try direct match
        if key in data:
            return data[key]
        
        # Try case-insensitive and stripped match
        for k, v in data.items():
            if k.strip().lower() == key_clean:
                return v
        
        return None
    
    def format_phone_number(self, phone_number: str) -> str:
        """
        Format phone number - removes all non-digit characters.
        🚀 IMPROVED: Handles strings with spaces by splitting and taking first valid segment.
        """
        if not phone_number:
            return ""
        
        # Convert to string and strip
        val = str(phone_number).strip()
        
        # 🔥 NEW: If contains spaces, take the first segment that looks like a number
        if " " in val:
            segments = val.split()
            for seg in segments:
                clean_seg = re.sub(r'\D', '', seg)
                if 8 <= len(clean_seg) <= 16:
                    return clean_seg
        
        # Remove all non-digit characters
        clean = re.sub(r'\D', '', val)
        
        if not clean:
            return ""

        # Valid WhatsApp numbers are usually 8-16 digits globally
        if len(clean) < 8 or len(clean) > 16:
            return ""
            
        return clean
    
    async def process_all_active_triggers(self):
        """
        🚀 Process all active triggers (Google Sheets AND Local Files)
        Unofficial WhatsApp API only.
        """
        logger.info("🔍 [AUTOMATION] Starting polling cycle for all active triggers...")
        try:
            # 1. Get all enabled triggers
            enabled_triggers = self.db.query(GoogleSheetTrigger).filter(
                GoogleSheetTrigger.is_enabled == True
            ).all()
            
            if not enabled_triggers:
                logger.info("ℹ️ No enabled triggers found in database.")
                return
            
            logger.info(f"🚀 Found {len(enabled_triggers)} enabled triggers to process.")
            
            for trigger in enabled_triggers:
                try:
                    rows_data = []
                    headers_data = []
                    sheet = None
                    
                    # CASE A: Google Sheet Based
                    if trigger.sheet_id:
                        sheet = self.db.query(GoogleSheet).filter(GoogleSheet.id == trigger.sheet_id).first()
                        if not sheet or sheet.status != SheetStatus.ACTIVE:
                            logger.warning(f"⚠️ Trigger {trigger.trigger_id} linked to missing or inactive sheet {trigger.sheet_id}")
                            continue
                        
                        try:
                            # Fetch Google Sheet data
                            rows_data, headers_data = await asyncio.to_thread(
                                self.sheets_service.get_sheet_data_with_headers,
                                spreadsheet_id=sheet.spreadsheet_id,
                                worksheet_name=sheet.worksheet_name or "Sheet1"
                            )
                        except Exception as sheet_err:
                            logger.error(f"❌ Failed to fetch Google Sheet data for trigger {trigger.trigger_id}: {sheet_err}")
                            continue

                    # CASE B: Local File Based (CSV/Excel)
                    elif trigger.source_file_url:
                        try:
                            rows_data, headers_data = self._load_local_file_data(trigger.source_file_url)
                            if not rows_data and not headers_data:
                                # This usually means file not found
                                logger.warning(f"⚠️ Trigger {trigger.trigger_id}: File not found or empty. Auto-pausing trigger.")
                                trigger.is_enabled = False
                                self.db.commit()
                                continue
                        except Exception as file_err:
                            logger.error(f"❌ Failed to load local file for trigger {trigger.trigger_id}: {file_err}")
                            continue
                    
                    else:
                        logger.warning(f"⚠️ Trigger {trigger.trigger_id} has neither sheet_id nor source_file_url - skipping")
                        continue

                    if not rows_data:
                        # No data to process for this trigger
                        continue
                    
                    # Process the trigger with the loaded data
                    await self.process_single_trigger(sheet, trigger, rows_data, headers_data)
                    
                except Exception as trigger_loop_error:
                    logger.error(f"❌ Error in trigger execution loop for {trigger.trigger_id}: {trigger_loop_error}")
                    continue
            
            logger.info("✅ Completed polling cycle")
            
        except Exception as e:
            logger.error(f"❌ Critical Error in process_all_active_triggers: {e}")
            if hasattr(self.db, 'rollback'):
                 self.db.rollback()
    
    async def process_sheet_triggers(self, sheet: GoogleSheet, rows_data: List[Dict[str, Any]], headers_data: List[str]):
        """
        Process all triggers for a specific sheet using unofficial WhatsApp API only
        """
        try:
            logger.info(f"📋 Processing triggers for sheet {sheet.sheet_name} ({sheet.id})")
            logger.info(f"   Sheet has {len(rows_data)} rows and {len(headers_data)} columns")
            
            # Get all enabled triggers for this sheet
            triggers = self.db.query(GoogleSheetTrigger).filter(
                and_(
                    GoogleSheetTrigger.sheet_id == sheet.id,
                    GoogleSheetTrigger.is_enabled == True
                )
            ).all()
            
            if not triggers:
                logger.info(f"   No enabled triggers found for sheet {sheet.sheet_name}")
                return
            
            logger.info(f"   Found {len(triggers)} enabled triggers")
            
            # Process each trigger
            for trigger in triggers:
                try:
                    await self.process_single_trigger(sheet, trigger, rows_data, headers_data)
                except Exception as trigger_error:
                    logger.error(f"   ❌ Error processing trigger {trigger.trigger_id}: {trigger_error}")
                    continue
            
            logger.info(f"✅ Completed processing triggers for sheet {sheet.sheet_name}")
            
        except Exception as e:
            logger.error(f"❌ Error processing sheet triggers: {e}")
    
    async def process_single_trigger(self, sheet: GoogleSheet, trigger: GoogleSheetTrigger, 
                                  rows_data: List[Dict[str, Any]], headers_data: List[str]):
        """
        Process a single trigger using unofficial WhatsApp API only
        """
        # 🔥 1. INITIALIZE COUNTERS (Fix match_count crash)
        match_count = 0
        processed_count = 0
        error_count = 0
        invalid_rows = 0
        total_rows = len(rows_data)
        
        # 🔥 CRITICAL FIX: Check for already processed rows to prevent multiple firings
        processed_rows = set()
        try:
            # Get history for this trigger from last 24 hours
            from datetime import datetime, timedelta
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
            recent_history = self.db.query(GoogleSheetTriggerHistory).filter(
                and_(
                    GoogleSheetTriggerHistory.trigger_id == str(trigger.trigger_id),
                    GoogleSheetTriggerHistory.triggered_at >= cutoff_time,
                    GoogleSheetTriggerHistory.status == TriggerHistoryStatus.SENT.value
                )
            ).all()
            
            # Extract row numbers that were already processed
            for history in recent_history:
                row_data = history.row_data or {}
                if isinstance(row_data, dict) and 'row_number' in row_data:
                    processed_rows.add(row_data['row_number'])
            
            logger.info(f"🔥 [DUPLICATE_CHECK] Found {len(processed_rows)} already processed rows in last 24h")
        except Exception as e:
            logger.warning(f"⚠️ [DUPLICATE_CHECK] Failed to check processed rows: {e}")

        try:
            # 🔥 2. PUBLIC MODE DETECTION
            is_public_mode = not getattr(self.sheets_service, 'has_real_credentials', False)
            if is_public_mode:
                logger.warning(f"⚠️ [AUTOMATION] Running in read-only (PUBLIC) mode for trigger {trigger.trigger_id}")

            # 🔥 3. STRICT HEADER VALIDATION
            headers = [str(h).strip() for h in headers_data]
            headers_lower = [h.lower() for h in headers]
            
            # Check for corruption (headers containing numbers)
            corrupted_headers = [h for h in headers if any(char.isdigit() for char in h)]
            if corrupted_headers and len(corrupted_headers) > len(headers) / 2:
                error_msg = f"❌ [VALIDATION ERROR] Sheet structure appears corrupted. Headers contain numbers: {corrupted_headers[:3]}"
                logger.error(error_msg)
                return

            # Ensure 'Phone' column exists
            phone_col = (trigger.phone_column or 'phone').strip().lower()
            if phone_col not in headers_lower:
                error_msg = f"❌ [VALIDATION ERROR] 'Phone' column missing. Trigger expected '{phone_col}', but headers are: {headers_lower}"
                logger.error(error_msg)
                return

            # 🔥 4. DEVICE HANDLING (No silent fallback)
            device_id = trigger.device_id or (getattr(sheet, 'device_id', None))
            multi_devices = (trigger.trigger_config or {}).get('multi_device_ids', [])
            
            if not device_id and not multi_devices:
                logger.warning(f"   ⚠️ Trigger {trigger.trigger_id} has no device_id - skipping execution.")
                return
            
            if not device_id and multi_devices:
                device_id = multi_devices[0]

            # Identify message owner
            triggered_by_user_id = trigger.user_id or (getattr(sheet, 'user_id', None))
            if not triggered_by_user_id:
                logger.error(f"   ❌ Trigger {trigger.trigger_id} has no user_id - skipping")
                return

            logger.info(f"🎯 [AUTOMATION] Processing Trigger: {trigger.trigger_id} ({trigger.trigger_type})")
            
            # Schedule check (Existing logic preserved)
            if trigger.trigger_type == "time" and trigger.scheduled_at:
                ist_tz = timezone(timedelta(hours=5, minutes=30))
                literal_time = trigger.scheduled_at.replace(tzinfo=None)
                sched_time_utc = literal_time.replace(tzinfo=ist_tz).astimezone(timezone.utc)
                now_utc = datetime.now(timezone.utc)
                
                if now_utc < sched_time_utc:
                    diff = sched_time_utc - now_utc
                    minutes_left = int(diff.total_seconds() / 60)
                    if minutes_left < 60:
                        logger.info(f"   ⏳ Trigger {trigger.trigger_id} waiting: {minutes_left}m until {literal_time.strftime('%H:%M')} IST")
                    return

            # Device Validation & Fallback (Only if explicitly handled)
            active_device_id = device_id
            device_validation = validate_device_before_send(self.db, active_device_id, user_id=triggered_by_user_id)
            
            if not device_validation["valid"]:
                logger.warning(f"   ⚠️ Primary device {active_device_id} issues: {device_validation.get('error')}. Checking Fallback...")
                fallback_candidates = self.db.query(Device).filter(Device.busi_user_id == triggered_by_user_id).all()
                fallback_device_id = None
                
                for candidate in fallback_candidates:
                    candidate_valid = validate_device_before_send(self.db, candidate.device_id, user_id=triggered_by_user_id)
                    if candidate_valid["valid"]:
                        fallback_device_id = candidate.device_id
                        break

                if fallback_device_id:
                    active_device_id = fallback_device_id
                else:
                    logger.error(f"   ❌ No connected devices found for user {triggered_by_user_id}. Skipping trigger.")
                    return

            # 🔥 5. ROW PROCESSING LOOP (SAFE)
            logger.info(f"📊 [AUTOMATION] Scanning {total_rows} rows...")
            
            for row in rows_data:
                try:
                    # Process row
                    res = await self.process_row_for_trigger(sheet, trigger, row, active_device_id, headers=headers_data, processed_rows=processed_rows)
                    
                    if isinstance(res, dict):
                        if res.get("match"):
                            match_count += 1
                        if res.get("processed"):
                            processed_count += 1
                        if res.get("reason") == "no_phone" or res.get("reason") == "invalid_phone":
                            invalid_rows += 1
                    else:
                        error_count += 1
                except Exception as row_e:
                    logger.error(f"   ❌ Error processing row {row.get('row_number')}: {row_e}")
                    error_count += 1
                    continue
            
            # Update last processed states
            if trigger.trigger_type == "new_row" and rows_data:
                max_row = max(row.get('row_number', 0) for row in rows_data)
                trigger.last_processed_row = max(trigger.last_processed_row, max_row)
            
            trigger.last_triggered_at = datetime.now(timezone.utc)
            self.db.commit()
            
            # 🔥 6. FINAL REPORT (User requested)
            report = f"""
📈 [FINAL REPORT] Trigger {trigger.trigger_id}
-----------------------------------
Total Rows:    {total_rows}
Valid Rows:    {total_rows - invalid_rows}
Invalid Rows:  {invalid_rows}
Matches Found: {match_count}
Sent/Processed: {processed_count}
Errors:        {error_count}
-----------------------------------
"""
            logger.info(report)
            
            # 🔥 FIX: Return processed count for tracking
            return processed_count
            
        except Exception as e:
            logger.error(f"   ❌ [AUTOMATION] Trigger {trigger.trigger_id} failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return 0
    
    async def process_row_for_trigger(self, sheet: GoogleSheet, trigger: GoogleSheetTrigger, row_info: Dict[str, Any], device_id: Any = None, headers: Optional[List[str]] = None, processed_rows: set = None):
        """
        Process a single row for trigger using unofficial WhatsApp API only
        """
        try:
            # Fallback to trigger.device_id if not passed
            device_id = device_id or trigger.device_id
            
            row_data = row_info['data']
            row_number = row_info['row_number']
            
            # 🔥 CRITICAL FIX: Initialize processed_rows if not passed
            if processed_rows is None:
                processed_rows = set()
                
            # 🔥 DUPLICATE CHECK: Skip if already processed
            if row_number in processed_rows:
                logger.info(f"   Row {row_number}: Already processed in last 24h. Skipping.")
                return {"processed": False, "reason": "already_processed"}
            
            # 🔥 NEW: Skip Empty Rows (Filter out filler rows at the bottom of sheets)
            phone_val = self.get_case_insensitive_value(row_data, trigger.phone_column or 'Phone')
            if not phone_val or str(phone_val).strip() == "":
                # Don't log as warning, just debug-level skip to keep logs clean
                logger.debug(f"   Row {row_number}: Skipped (No phone number found)")
                return {"processed": False, "reason": "empty_row"}

            # 🔥 NEW: Early Local History Check (Crucial for Public Mode)
            # If we've already handled this row locally, skip it immediately unless data changed or manually reset
            try:
                # Search for records for this trigger + row
                history_records = self.db.query(GoogleSheetTriggerHistory).filter(
                    GoogleSheetTriggerHistory.trigger_id == str(trigger.trigger_id)
                ).all()
                
                trigger_match_value = str(trigger.trigger_value or "Send").strip().lower()
                status_column = trigger.status_column or 'Status'
                current_raw_status = self.get_case_insensitive_value(row_data, status_column)
                current_normalized_status = str(current_raw_status or "").strip().lower()

                for h in history_records:
                    if h.row_data and h.row_data.get('row_number') == row_number:
                        # 1. Check if it's an EXACT duplicate that was recently sent
                        # We compare the data (excluding the status column)
                        prev_data = h.row_data.get('data', {})
                        
                        # Remove status from comparison
                        curr_comp_data = {k: v for k, v in row_data.items() if k.lower() != status_column.lower()}
                        prev_comp_data = {k: v for k, v in prev_data.items() if k.lower() != status_column.lower()}
                        
                        is_exact_data_duplicate = (curr_comp_data == prev_comp_data)
                        
                        # If it's the exact same content and it was already sent...
                        if is_exact_data_duplicate and h.status == "sent":
                            # EXCEPT if the user has manually set the status back to the trigger value
                            # and it's been more than 10 minutes (to prevent infinite loops in Public Mode)
                            if current_normalized_status == trigger_match_value:
                                ten_min_ago = datetime.now(timezone.utc) - timedelta(minutes=10)
                                if h.triggered_at and h.triggered_at.replace(tzinfo=timezone.utc) < ten_min_ago:
                                    logger.info(f"   🔄 Row {row_number}: Manual reset detected (Trigger value '{current_raw_status}' after 10m). Re-processing.")
                                    # We don't break, we allow it to proceed to the next checks
                                    continue
                                else:
                                    # It's an exact duplicate and too recent
                                    logger.info(f"   Row {row_number}: ⏭️ Skipped (Duplicate content sent {h.triggered_at}. Cooldown 10m active.)")
                                    return {"processed": False, "match": True, "reason": "duplicate_prevented"}
                            else:
                                logger.info(f"   Row {row_number}: ⏭️ Skipped (Already handled recently)")
                                return {"processed": False, "match": True, "reason": "already_handled_locally"}
                        
                        # 2. If data has CHANGED, we allow it even if previously sent
                        if not is_exact_data_duplicate and h.status == "sent":
                             logger.info(f"   📝 Row {row_number}: Data change detected. Re-processing trigger.")
                             continue

            except Exception as hist_err:
                logger.warning(f"   ⚠️ Row {row_number}: Smart history check error: {hist_err}")

            # Skip if already processed (Only for new_row triggers)
            if trigger.trigger_type == "new_row" and row_number <= trigger.last_processed_row:
                logger.debug(f"   Row {row_number}: Skipped (Already processed: {trigger.last_processed_row})")
                return {"processed": False, "reason": "already_processed"}
            
            # Identify message owner
            row_owner_id = str(getattr(sheet, 'user_id', trigger.user_id))
            
            logger.info(f"   Row {row_number}: Inspecting row data: {row_data}")
            
            # 🔥 CRITICAL: Common status check for both time and status triggers
            status_column = trigger.status_column or 'Status'
            raw_status = self.get_case_insensitive_value(row_data, status_column)
            normalized_status = str(raw_status or "").strip().lower()
            
            # 1. Skip if already marked as finished in the sheet
            # 🔥 FIX: Remove 'send' and 'sent' from defensive skip if they are the trigger value!
            ALREADY_HANDLED = ['processing', 'success', 'delivered', 'done', 'failed', 'expired']
            if normalized_status in ALREADY_HANDLED and normalized_status != str(trigger.trigger_value or "").lower():
                # No need to log this every time for every column
                return {"processed": False, "reason": "already_handled"}
            
            # 2. Check in-memory lock (prevent concurrency issues)
            # Use trigger_id + row_number to be unique across sheets and files
            row_lock_key = f"trig_{trigger.trigger_id}_row_{row_number}"
            if row_lock_key in self._processing_rows:
                logger.warning(f"   Row {row_number}: Skipped (Already being processed in this cycle)")
                return {"processed": False, "reason": "already_processing_memory"}

            # Mark as processing in memory
            self._processing_rows.add(row_lock_key)
            
            try:
                logger.debug(f"   Row {row_number}: Current status is '{normalized_status}' - proceeding with trigger check")

                # Handle trigger-specific conditions
                if trigger.trigger_type == "time":
                    # If we have a global scheduled_at, we already checked it in process_single_trigger
                    # So we just proceed to send this row if it doesn't have its own per-row Send_time column
                    if trigger.scheduled_at:
                        logger.info(f"   🎯 Row {row_number}: Processing via Global Schedule")
                        # 🔥 IST Aware Interpretation:
                        # Stored as '15:13+00:00', but we treat '15:13' as IST and convert to real UTC.
                        ist_tz = timezone(timedelta(hours=5, minutes=30))
                        literal_time = trigger.scheduled_at.replace(tzinfo=None)
                        send_time_value = literal_time.replace(tzinfo=ist_tz).astimezone(timezone.utc)
                    else:
                        # Fallback to old per-row column logic if global schedule is not set
                        send_time_value = self.get_case_insensitive_value(row_data, trigger.send_time_column)
                        
                        if not send_time_value:
                            logger.warning(f"   Row {row_number}: No send_time value in column '{trigger.send_time_column}'.")
                            return {"processed": False, "reason": "no_send_time"}
                    
                    # Parse send_time and check if it's time to send
                    try:
                        # 🔥 TIMEBASE RELIABILITY FIX (UTC Comparisons)
                        now_utc = datetime.now(timezone.utc)
                        ist_tz = timezone(timedelta(hours=5, minutes=30))
                        today_ist = now_utc.astimezone(ist_tz).date()
                        
                        if isinstance(send_time_value, (int, float)):
                            # 🔥 GOOGLE SHEETS SERIAL DATE FIX: 
                            # Excel/Google Sheets dates are days since 1899-12-30
                            # 0.5 = 12:00 PM, 45376.5 = 2024-03-25 12:00 PM
                            try:
                                base_date = datetime(1899, 12, 30)
                                send_time_raw = base_date + timedelta(days=float(send_time_value))
                                
                                # If it's just a time (value < 1), attach today's IST date
                                if float(send_time_value) < 1:
                                    send_time = datetime.combine(today_ist, send_time_raw.time())
                                else:
                                    send_time = send_time_raw
                            except:
                                logger.error(f"   ❌ Row {row_number}: Could not convert numeric time '{send_time_value}'")
                        
                        elif isinstance(send_time_value, str):
                            s = send_time_value.strip().upper()
                            
                            # Fix common formatting issues
                            s = s.replace("  ", " ") # Remove double spaces
                            
                            formats = [
                                '%H:%M:%S', '%H:%M',           # 24-hour
                                '%I:%M:%S %p', '%I:%M %p',     # 12-hour with AM/PM
                                '%H:%M:%S %p', '%H:%M %p',     # Tolerant 24-hour + AM/PM
                                '%d-%m-%Y %H:%M:%S', '%d-%m-%Y %H:%M', # Indian/Common with date
                                '%d/%m/%Y %H:%M:%S', '%d/%m/%Y %H:%M', # Slab/Slash format
                                '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', # ISO with date (space separator)
                                '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M', # ISO with date ('T' separator)
                                '%Y-%m-%d %I:%M:%S %p', '%Y-%m-%d %I:%M %p', # ISO + AM/PM
                            ]
                            
                            for fmt in formats:
                                try:
                                    parsed = datetime.strptime(s, fmt)
                                    # If the format only contained time (year defaults to 1900), attach today's date
                                    if parsed.year == 1900:
                                        # Use IST today
                                        ist_tz = timezone(timedelta(hours=5, minutes=30))
                                        today_ist = datetime.now(timezone.utc).astimezone(ist_tz).date()
                                        send_time = datetime.combine(today_ist, parsed.time()).replace(tzinfo=ist_tz)
                                    else:
                                        # Assume date is in IST if no tz info
                                        ist_tz = timezone(timedelta(hours=5, minutes=30))
                                        send_time = parsed.replace(tzinfo=ist_tz)
                                    break
                                except ValueError:
                                    continue
                                    
                            if not send_time:
                                # Last resort: Try regex for weird formats like 17:38:00 PM
                                match = re.search(r'(\d{1,2}):(\d{1,2})(?::(\d{1,2}))?\s*(AM|PM)?', s)
                                if match:
                                    h = int(match.group(1))
                                    m = int(match.group(2))
                                    s_val = int(match.group(3)) if match.group(3) else 0
                                    ampm = match.group(4)
                                    
                                    if ampm == 'PM' and h < 12: 
                                        h += 12
                                    elif ampm == 'AM' and h == 12: 
                                        h = 0
                                        
                                    send_time = datetime.combine(today_ist, time(h, m, s_val))
                        
                        elif isinstance(send_time_value, (time, datetime)):
                            send_time = datetime.combine(today_ist, send_time_value) if isinstance(send_time_value, time) else send_time_value
                        
                        if not send_time:
                            raise ValueError(f"Could not parse time format: '{send_time_value}'")
                        
                        # Normalize everything to aware UTC for final comparison
                        if send_time.tzinfo is None:
                            # Default to IST if unspecified (common for user-input times)
                            ist_tz = timezone(timedelta(hours=5, minutes=30))
                            send_time = send_time.replace(tzinfo=ist_tz)
                        
                        now_utc = datetime.now(timezone.utc)
                        send_time_utc = send_time.astimezone(timezone.utc)
                        
                        # Use literal IST for logging to be clear for the user
                        ist_tz = timezone(timedelta(hours=5, minutes=30))
                        sched_ist_str = send_time_utc.astimezone(ist_tz).strftime('%H:%M')
                        
                        logger.info(f"   Row {row_number}: Time Check -> Schedule: {sched_ist_str} IST, Current IST: {now_utc.astimezone(ist_tz).strftime('%H:%M')}")
                        
                        if now_utc < send_time_utc:
                            # logger.info(f"   Row {row_number}: Time {send_time_utc} not reached yet.")
                            return {"processed": False, "reason": "time_not_reached"}
                            
                        # 🔥 RELIABILITY FIX: Expand window to 24 hours for triggered rows
                        if now_utc > send_time_utc + timedelta(hours=24):
                            logger.warning(f"   Row {row_number}: Time {send_time_utc} has expired (>24h). Will not send.")
                            
                            await self.create_trigger_history(
                                sheet, trigger, row_number, "", "", TriggerHistoryStatus.FAILED, 
                                f"Time expired (>24h window). Missed window for {send_time_utc}",
                                device_id=device_id,
                                full_row_data=row_data
                            )
                            # Update sheet status to Expired 
                            await self.update_sheet_status(sheet, row_number, trigger.status_column, 'Expired')
                            
                            return {"processed": True, "reason": "time_expired"}

                        logger.info(f"   Row {row_number}: ⏰ Time Trigger Match! {send_time_utc} <= {now_utc}")
                        
                    except Exception as e:
                        logger.error(f"   ❌ Row {row_number}: Time parse error: {e}")
                        await self.create_trigger_history(
                            sheet, trigger, row_number, "", "", TriggerHistoryStatus.FAILED, 
                            f"Invalid time format: {send_time_value}",
                            device_id=device_id,
                            full_row_data=row_data
                        )
                        return {"processed": False, "reason": "invalid_time"}
                
                # 🔥 STATUS CHECK LOGIC - Different for time vs status triggers
                    status_col_name = trigger.status_column or 'Status'
                    raw_status = self.get_case_insensitive_value(row_data, status_col_name)
                    
                    normalized_status = str(raw_status or "").strip().lower()
                    
                    # For time-based triggers, allow empty/None status values
                    # Only require status matching for status-based triggers
                    process_row = False
                    match_result = "NO"
                    
                    if trigger.trigger_type == "time":
                        # Time triggers: allow empty status or any status that's not already handled
                        if not normalized_status or normalized_status in ["", "none"]:
                            # Empty status is OK for time triggers
                            process_row = True
                            match_result = "YES (empty OK for time trigger)"
                        elif normalized_status in ["send", "yes", "true", "1"]:
                            # Explicit send status is also OK
                            process_row = True
                            match_result = "YES"
                        else:
                            # Check if it's an already handled status
                            ALREADY_HANDLED = ['processing', 'success', 'delivered', 'done', 'failed', 'expired', 'sent']
                            if normalized_status in ALREADY_HANDLED:
                                process_row = False
                                match_result = "NO (already handled)"
                            else:
                                # Unknown status but not already handled - allow it for time triggers
                                process_row = True
                                match_result = "YES (unknown status OK for time trigger)"
                    else:
                        # Status-based triggers: require exact match
                        valid_status = ["send", "yes", "true", "1"]
                        trigger_value = str(trigger.trigger_value or "").strip().lower()
                        
                        # Use trigger_value if set, otherwise use valid_status defaults
                        if trigger_value:
                            valid_status = [trigger_value]
                        
                        if normalized_status in valid_status:
                            process_row = True
                            match_result = "YES"
                        else:
                            process_row = False
                    
                    # [ROW DEBUG] Logging
                    logger.info(f"\n[ROW DEBUG]\nRow: {row_number}\nRaw Status: \"{raw_status}\"\nCleaned: \"{normalized_status}\"\nMatch: {match_result}")
                    
                    if not process_row:
                        logger.info(f"   Row {row_number}: ⏭️ Skipped due to Status mismatch ('{raw_status}')")
                        return {"processed": False, "match": False, "reason": "status_mismatch"}
                    
                    logger.info(f"   🎯 Row {row_number}: Match found! Status '{raw_status}' matched.")
                
                # Extract phone number
                phone_column = trigger.phone_column or 'phone'
                phone = self.get_case_insensitive_value(row_data, phone_column)
                
                if not phone:
                    logger.warning(f"   Row {row_number}: No phone number in column '{phone_column}'. Available: {list(row_data.keys())}")
                    await self.create_trigger_history(
                        sheet, trigger, row_number, "", "", TriggerHistoryStatus.FAILED, 
                        f"No phone number found in column {phone_column}",
                        device_id=device_id
                    )
                    return {"processed": False, "reason": "no_phone"}
                
                # Format phone number
                formatted_phone = self.format_phone_number(str(phone))
                
                # 🔥 NEW: ROUND ROBIN & RANDOM DELAY
                import random
                
                # 1. Handle Multi-Template Cycling
                # If trigger_config has multi_templates, pick current and cycle
                config = trigger.trigger_config or {}
                multi_templates = config.get('multi_templates', [])
                
                if multi_templates:
                    current_t_idx = config.get('current_template_idx', 0)
                    if current_t_idx >= len(multi_templates):
                        current_t_idx = 0
                    
                    # Use template with processing
                    raw_template = multi_templates[current_t_idx]
                    message = self.sheets_service.process_message_template(raw_template, row_data)
                    logger.info(f"   📝 [ROUND ROBIN] Using Template {current_t_idx + 1} of {len(multi_templates)}: {raw_template[:50]}...")
                else:
                    # Original logic: prioritize message column over single template
                    message = ""
                    if trigger.message_column:
                        message_val = self.get_case_insensitive_value(row_data, trigger.message_column)
                        if message_val is not None:
                            message = str(message_val).strip()
                            if message:
                                logger.info(f"   📝 Using message from column '{trigger.message_column}': '{message[:50]}...'")
                    
                    if not message and trigger.message_template:
                        message = self.sheets_service.process_message_template(trigger.message_template, row_data)
                        logger.info(f"   📝 Using message template: '{message[:50]}...'")

                # Check if this is a media-only case (empty template but has media)
                if message == "" and trigger.media_url:
                    logger.info(f"   📎 [MEDIA-ONLY] Sending media without caption")
                    # Keep message as empty string for media-only
                elif not message:
                    error_msg = "No message content available"
                    logger.error(f"   ❌ Row {row_number}: {error_msg}")
                    await self.create_trigger_history(sheet, trigger, row_number, formatted_phone, "", TriggerHistoryStatus.FAILED, error_msg, device_id=device_id, full_row_data=row_data)
                    return {"processed": False, "reason": "no_message"}

                # 2. Handle Multi-Device Rotation
                multi_devices = config.get('multi_device_ids', [])
                if multi_devices:
                    current_d_idx = config.get('current_device_idx', 0)
                    if current_d_idx >= len(multi_devices):
                        current_d_idx = 0
                    
                    device_id = multi_devices[current_d_idx]
                    logger.info(f"   🎯 [ROUND ROBIN] Using Device {current_d_idx + 1} of {len(multi_devices)}: {device_id}")
                
                # 3. Randomized Delay (15-30s) - Human-like delivery
                # We only delay if it's NOT the very first successful send of this whole cycle to keep it responsive,
                # but for safety let's just always apply if it's within a loop.
                # Actually, most users want it to happen BETWEEN sends.
                if hasattr(self, '_last_send_time'):
                    # Check if last send was very recent
                    time_since_last = (datetime.now() - self._last_send_time).total_seconds()
                    if time_since_last < 5: # If we are processing rapidly
                        delay = random.uniform(15, 30)
                        logger.info(f"   ⏳ [STAGGERED] Waiting {delay:.1f}s before sending next...")
                        await asyncio.sleep(delay)

                # 🔥 RACE CONDITION FIX: Fetch the LATEST status right before processing (Sheets Only)
                status_column = trigger.status_column or 'Status'
                if sheet and sheet.spreadsheet_id:
                    try:
                        # Clear cache to get fresh data
                        cache_key = f"{sheet.spreadsheet_id}:{sheet.worksheet_name or 'Sheet1'}"
                        if cache_key in self.sheets_service._sheet_cache:
                            del self.sheets_service._sheet_cache[cache_key]
                        
                        fresh_rows, _ = await asyncio.to_thread(
                            self.sheets_service.get_sheet_data_with_headers,
                            sheet.spreadsheet_id,
                            sheet.worksheet_name
                        )
                        
                        matching_row = next((r for r in fresh_rows if r['row_number'] == row_number), None)
                        if matching_row:
                            latest_status = str(self.get_case_insensitive_value(matching_row['data'], status_column) or "").strip().lower()
                            if latest_status in ALREADY_HANDLED:
                                logger.info(f"   Row {row_number}: 🛑 SKIPPED - Status changed to '{latest_status}' by another process.")
                                return {"processed": False, "reason": "already_handled_race_win"}
                    except Exception as e:
                        logger.warning(f"   ⚠️ Row {row_number}: Could not verify fresh status: {e}")

                # Step 1: Update sheet status to "Processing"
                # 🔥 SAFETY: Respect Public Mode or File-based (No Update)
                if not sheet:
                    logger.info(f"   ✨ Row {row_number}: [FILE-BASED] Skipping sheet status update")
                    status_updated = True
                elif not getattr(self.sheets_service, 'has_real_credentials', False):
                    logger.info(f"   ✨ Row {row_number}: [PUBLIC MODE] Skipping sheet status update to 'Processing'")
                    status_updated = True # Bypassed
                else:
                    status_updated = await self.update_sheet_status(sheet, row_number, status_column, "Processing", headers)
                
                if not status_updated:
                    logger.warning(f"   ⚠️ Row {row_number}: Skipping send because sheet status could not be updated to 'Processing'")
                    return {"processed": False, "reason": "status_update_failed"}
                
                # Step 2: Send WhatsApp message via unified service (to handle credits)
                try:
                    logger.info(f"   📤 Sending WhatsApp message for row {row_number} (Credit Aware)")
                    logger.info(f"   Phone: {formatted_phone}")
                    logger.info(f"   Device: {device_id}")
                    logger.info(f"   User ID: {row_owner_id}")
                    
                    # Create unified message request with media support
                    message_type = MessageType.TEXT
                    media_url = None
                    
                    # 🔥 IMPROVED MEDIA PROCESSING & VALIDATION
                    message_type = MessageType.TEXT
                    media_url = None
                    
                    if trigger.media_url:
                        media_detected = True
                        logger.info(f"   📎 Media detected: {trigger.media_url}")
                        
                        # 1. Detect media type
                        media_type_lower = (trigger.media_type or "").lower().strip()
                        if not media_type_lower:
                            # Try to detect from URL extension
                            ext = os.path.splitext(trigger.media_url)[1].lower()
                            if ext in ['.jpg', '.jpeg', '.png', '.gif']:
                                media_type_lower = 'image'
                            elif ext in ['.mp4', '.avi', '.mov']:
                                media_type_lower = 'video'
                            elif ext in ['.mp3', '.wav', '.ogg']:
                                media_type_lower = 'audio'
                            else:
                                media_type_lower = 'document'
                        
                        if media_type_lower in ['image', 'images', 'jpg', 'jpeg', 'png', 'gif']:
                            message_type = MessageType.IMAGE
                        elif media_type_lower in ['video', 'videos', 'mp4', 'avi', 'mov']:
                            message_type = MessageType.VIDEO
                        elif media_type_lower in ['audio', 'audio', 'mp3', 'wav', 'ogg']:
                            message_type = MessageType.AUDIO
                        else:
                            message_type = MessageType.DOCUMENT
                        
                        # 2. Normalize and check path
                        media_url = trigger.media_url
                        if media_url.startswith('http://localhost:8000/uploads/'):
                            media_path = media_url.replace('http://localhost:8000/uploads/', 'uploads/')
                        elif media_url.startswith('http://127.0.0.1:8000/uploads/'):
                            media_path = media_url.replace('http://127.0.0.1:8000/uploads/', 'uploads/')
                        else:
                            media_path = media_url
                            
                        # 3. Path Accessibility Validation
                        if os.path.exists(media_path):
                            logger.info(f"   ✅ Media file validated and accessible: {media_path}")
                            media_url = media_path
                        else:
                            # If it's a real HTTP URL (remote), we keep it as is, otherwise log warning
                            if not media_url.startswith('http'):
                                logger.warning(f"   ⚠️ Media file not found or inaccessible at path: {media_path}")
                                # We'll still try to send it, the engine will handle the final error
                        
                        media_payload = {
                            "type": message_type.value,
                            "file": media_url
                        }
                        logger.info(f"   Media payload structured: {media_payload}")
                    else:
                        logger.info(f"   No media detected - sending text only")
                    
                    msg_request = UnifiedMessageRequest(
                        to=formatted_phone,
                        type=message_type,
                        message=message,
                        media_url=media_url,
                        device_id=str(device_id),
                        user_id=row_owner_id
                    )
                    
                    logger.info(f"   Created message request - type: {message_type}, media_url: {media_url}")
                    
                    # Send via unified service which handles credits and balance checks
                    # 🔥 SYNC-IN-ASYNC FIX: Wrap blocking call in thread
                    send_response = await asyncio.to_thread(
                        self.unified_service.send_unified_message, 
                        msg_request
                    )
                    
                    if send_response.success:
                        # Step 3: Update sheet status to "Sent"
                        await self.update_sheet_status(sheet, row_number, status_column, "Sent", headers)
                        # 🔥 CRITICAL: Update local data so other triggers in same loop skip this
                        row_data[status_column] = "Sent"
                        
                        # Step 4: Save trigger history
                        await self.create_trigger_history(
                            sheet, trigger, row_number, formatted_phone, message, 
                            TriggerHistoryStatus.SENT, message_id=send_response.message_id,
                            device_id=device_id,
                            full_row_data=row_data
                        )
                        
                        logger.info(f"   ✅ Row {row_number}: Message sent successfully via Unified Service")
                        
                        # 🔥 AFTER SUCCESSFUL SEND: Update Round Robin Indices & Track Last Send
                        self._last_send_time = datetime.now()
                        
                        config = trigger.trigger_config or {}
                        multi_templates = config.get('multi_templates', [])
                        multi_devices = config.get('multi_device_ids', [])
                        
                        if multi_templates or multi_devices:
                            # 🔥 CRITICAL FIX: Properly update round-robin indices
                            if multi_templates:
                                config['current_template_idx'] = (config.get('current_template_idx', 0) + 1) % len(multi_templates)
                            if multi_devices:
                                config['current_device_idx'] = (config.get('current_device_idx', 0) + 1) % len(multi_devices)
                            
                            # 🔥 CRITICAL FIX: Commit the config changes to DB
                            trigger.trigger_config = config
                            self.db.commit()
                            logger.info(f"   🔄 [ROUND ROBIN] Updated indices - Template: {config.get('current_template_idx', 0)}, Device: {config.get('current_device_idx', 0)}")
                        
                        return {"processed": True, "status": "sent", "match": True}
                        
                    else:
                        raise Exception("Unified service reported failure without exception")
                        
                except Exception as e:
                    # Step 3: Update sheet status to "Failed"
                    # Log the specific error (could be insufficient credits)
                    error_msg = str(e).replace("WhatsApp Engine error: ", "")
                    await self.update_sheet_status(sheet, row_number, status_column, "Failed", headers)
                    row_data[status_column] = "Failed"
                    
                    # Step 4: Save trigger history
                    await self.create_trigger_history(
                        sheet, trigger, row_number, formatted_phone, message, 
                        TriggerHistoryStatus.FAILED, error_message=error_msg,
                        device_id=device_id,
                        full_row_data=row_data
                    )
                    
                    logger.error(f"   ❌ Row {row_number}: Send failed - {error_msg}")
                    return {"processed": True, "status": "failed"}
                    
            except Exception as inner_e:
                logger.error(f"   ❌ Row {row_number}: Internal processing error - {inner_e}")
                return {"processed": False, "reason": "internal_error", "error": str(inner_e)}
            finally:
                # 🔓 RELEASE LOCK
                if row_lock_key in self._processing_rows:
                    self._processing_rows.remove(row_lock_key)
                    
        except Exception as outer_e:
            logger.error(f"   ❌ Row {row_number}: Outer processing error - {outer_e}")
            return {"processed": False, "reason": "outer_error", "error": str(outer_e)}
    
    async def update_sheet_status(self, sheet: GoogleSheet, row_number: int, status_column: str, status: str, headers: Optional[List[str]] = None) -> bool:
        """
        Update Google Sheet row status using the sheets service
        Returns True if update succeeded, False otherwise
        """
        try:
            if not sheet or not sheet.spreadsheet_id:
                # For file-based triggers, we skip sheet status update by returning True
                return True

            # 🔥 SILENT SKIP IN PUBLIC MODE: Provide a helpful hint
            if not getattr(self.sheets_service, 'has_real_credentials', False):
                 logger.info(f"   ℹ️ Row {row_number}: Status '{status}' saved to your DASHBOARD (Spreadsheet is READ-ONLY in Public Mode).")
                 return False

            # 🔥 FIX: Use worksheet_name (tab name) instead of sheet_name (descriptive name)
            target_worksheet = sheet.worksheet_name or "Sheet1"
            
            # 🔥 SYNC-IN-ASYNC FIX: Use to_thread for Google Sheets blocking call
            success = await asyncio.to_thread(
                self.sheets_service.update_cell,
                sheet.spreadsheet_id,
                target_worksheet,
                row_number,
                status_column,
                status,
                headers=headers
            )
            if success:
                logger.info(f"   📝 Updated row {row_number} status to '{status}' in column '{status_column}'")
                return True
            else:
                # Don't log error here as update_cell already logs it.
                return False
        except Exception as e:
            # Only log error if we have credentials
            if sheet and getattr(self.sheets_service, 'has_real_credentials', False):
                logger.error(f"   ❌ Error updating sheet status for row {row_number}: {e}")
            return False
    
    async def create_trigger_history(self, sheet: GoogleSheet, trigger: GoogleSheetTrigger, 
                                 row_number: int, phone: str, message: str, 
                                 status: TriggerHistoryStatus, message_id: Optional[str] = None, 
                                 error_message: Optional[str] = None, device_id: Any = None,
                                 full_row_data: Optional[Dict[str, Any]] = None):
        """
        Save trigger history after every row
        """
        try:
            from datetime import datetime
            history = GoogleSheetTriggerHistory(
                sheet_id=getattr(sheet, 'id', None),
                trigger_id=str(trigger.trigger_id),  # ✅ Cast UUID to string
                device_id=str(device_id or trigger.device_id), # ✅ Cast to string
                phone_number=phone,
                message_content=message,
                status=status.value,
                error_message=error_message,
                triggered_at=datetime.now(timezone.utc),  # ✅ Consistent UTC/IST handling
                row_data={
                    "row_number": row_number,
                    "trigger_id": str(trigger.trigger_id),
                    "message_id": message_id,
                    "data": full_row_data # 🔥 STORE FULL DATA FOR CHANGE DETECTION
                }
            )
            
            # 🔥 SYNC-IN-ASYNC FIX: Wrap DB commits in thread
            def save_history():
                self.db.add(history)
                self.db.commit()
            
            await asyncio.to_thread(save_history)
            
            logger.debug(f"   📋 Saved trigger history for row {row_number}: {status.value}")
            
        except Exception as e:
            logger.error(f"   Failed to save trigger history: {e}")
            self.db.rollback()

# Create alias for backward compatibility
GoogleSheetsAutomationService = GoogleSheetsAutomationServiceUnofficial
