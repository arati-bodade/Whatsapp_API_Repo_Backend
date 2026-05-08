from typing import List, Dict, Any, Optional, Tuple
import json
import logging
import re
from datetime import datetime, timedelta
from utils.template_engine import render_template

# Safe Google SDK imports with fallback
try:
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_SDK_AVAILABLE = True
except ImportError:
    GOOGLE_SDK_AVAILABLE = False
    Credentials = None
    build = None
    HttpError = None
    
import os
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Define credentials path
CREDENTIALS_FILE = "credentials/google-service-account.json"
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

from core.config import settings
from models.google_sheet import GoogleSheet, GoogleSheetTrigger, GoogleSheetTriggerHistory, SheetStatus, TriggerType, TriggerHistoryStatus
from schemas.google_sheet import RowProcessingResult
from utils.phone_utils import normalize_phone

logger = logging.getLogger(__name__)

class GoogleSheetsService:
    def __init__(self):
        if not GOOGLE_SDK_AVAILABLE:
            logger.warning("Google SDK not available. Google Sheets integration will be disabled.")
            self.sdk_available = False
            return
            
        self.sdk_available = True
        
        # Verify credentials file exists and check for placeholders ONCE
        self.has_real_credentials = False
        if not os.path.exists(CREDENTIALS_FILE):
             logger.warning(f"Service Account JSON not found at: {os.path.abspath(CREDENTIALS_FILE)}. Using Public Fallback if available.")
        else:
             try:
                 with open(CREDENTIALS_FILE, 'r') as f:
                     creds_data = f.read()
                 if "REPLACE_WITH_YOUR_REAL" in creds_data:
                     logger.warning("📝 NOTE: Google Sheets is in 'Public Mode' because placeholders are detected in credentials. Status updates (Sent/Processing) will not be saved to your sheet. Use the Guide to enable full access.")
                     self.has_real_credentials = False
                 else:
                     logger.info(f"✅ Service Account JSON found at: {os.path.abspath(CREDENTIALS_FILE)}")
                     self.has_real_credentials = True
             except Exception as e:
                 logger.error(f"Error reading credentials file: {e}")
                 self.has_real_credentials = False

        # 🔥 SILENCE SSL WARNINGS
        try:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        except:
            pass

    def normalize_sheet_status(self, status) -> str:
        """
        🔥 RULE 1: Normalize sheet status
        
        ❌ Current (galat):
        if row.status == "Pending":
        
        ✅ Fix (MUST):
        status = row.status.strip().lower()
        
        if status in ["pending", ""]:
            send_message()
        
        📌 Sheet me:
        "Pending"
        "pending "
        ""
        sab valid honge
        """
        if status is None:
            return ""
        
        # Convert to string and normalize
        status = str(status).strip().lower()
        
        # Return normalized status
        return status
    
    def is_eligible_for_sending(self, status) -> bool:
        """
        Check if a row status is eligible for sending messages
        """
        normalized_status = self.normalize_sheet_status(status)
        
        # Eligible statuses: empty, "pending", or variations
        eligible_statuses = ["", "pending"]
        
        return normalized_status in eligible_statuses

    def get_service_account_credentials(self) -> Optional[Credentials]:
        """Load credentials from Environment Variable or Service Account JSON file"""
        if not self.sdk_available:
            return None
            
        try:
            # 1. Try Environment Variable First (Best for Render/Vercel)
            env_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
            if env_json:
                try:
                    info = json.loads(env_json)
                    return Credentials.from_service_account_info(info, scopes=SCOPES)
                except Exception as e:
                    logger.error(f"Failed to load credentials from GOOGLE_SERVICE_ACCOUNT_JSON env var: {e}")

            # 2. Try Local File
            if not os.path.exists(CREDENTIALS_FILE) or not getattr(self, 'has_real_credentials', False):
                return None

            creds = Credentials.from_service_account_file(
                CREDENTIALS_FILE, 
                scopes=SCOPES
            )
            return creds
        except Exception as e:
            # Only log if we thought we had real credentials
            if getattr(self, 'has_real_credentials', False):
                logger.error(f"Failed to load Service Account credentials: {e}")
            return None

    # Helper to get authenticated service
    def get_service(self):
        """Get authenticated Google Sheets service using Service Account"""
        creds = self.get_service_account_credentials()
        if not creds:
             raise Exception("Could not load Service Account credentials")
        return build('sheets', 'v4', credentials=creds)
    
    def get_spreadsheet_info(self, credentials: Credentials, spreadsheet_id: str) -> Dict[str, Any]:
        """Get spreadsheet metadata"""
        try:
            service = self.get_sheets_service(credentials)
            spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            
            return {
                'spreadsheet_id': spreadsheet_id,
                'title': spreadsheet.get('properties', {}).get('title', 'Untitled'),
                'sheets': [
                    {
                        'name': sheet.get('properties', {}).get('title', 'Sheet1'),
                        'index': sheet.get('properties', {}).get('index', 0),
                        'grid_properties': sheet.get('properties', {}).get('gridProperties', {})
                    }
                    for sheet in spreadsheet.get('sheets', [])
                ]
            }
        except HttpError as e:
            logger.error(f"Failed to get spreadsheet info: {e}")
            raise
    
    def get_available_sheets(self, credentials: Optional[Credentials], spreadsheet_id: str) -> List[str]:
        """Fetch all available worksheet names from the spreadsheet"""
        try:
            # 1. Try official API first (Highest accuracy)
            creds = credentials or self.get_service_account_credentials()
            if creds:
                service = build('sheets', 'v4', credentials=creds)
                spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
                return [sheet.get('properties', {}).get('title', 'Unknown') for sheet in spreadsheet.get('sheets', [])]
        except Exception as e:
            logger.warning(f"⚠️  API Metadata fetch failed for {spreadsheet_id}: {e}. Trying PUBLIC SCANNER fallback.")

        # 🔥 2. PUBLIC SCANNER FALLBACK (Regex HTML Scraper)
        # This scans the public webpage of the sheet for tab names
        try:
            import requests
            import re
            
            public_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"
            res = requests.get(public_url, timeout=15)
            
            if res.status_code == 200:
                html = res.text
                # Google Sheets stores tab names in a JSON structure like: {"name":"Sheet1","id":0}
                # We'll use regex to extract all "name" values associated with sheets
                tab_matches = re.findall(r'\{"name":"([^"]+)","id":(\d+)\}', html)
                
                if tab_matches:
                    tab_names = [match[0] for match in tab_matches]
                    # Filter out common false positives if necessary, but usually this is accurate
                    logger.info(f"✨ Public Scanner Success: Found {len(tab_names)} tabs: {tab_names}")
                    return tab_names
                else:
                    # Final fallback if regex fails but page loaded
                    logger.warning(f"⚠️  Scanned public page but found no tabs. Defaulting to 'Sheet1'.")
                    return ["Sheet1"]
            else:
                 logger.error(f"❌ Public page not accessible (Status {res.status_code}). Sheet might be Private.")
        except Exception as scan_e:
            logger.error(f"❌ Public Scanner failed: {scan_e}")

        # If all fail, let the user know why
        raise Exception("Spreadsheet not accessible: Could not load Service Account credentials AND sheet is not Public.")
            
    def get_service_account_email(self) -> str:
        """Helper to get the email from credentials file for sharing instructions"""
        try:
            with open(CREDENTIALS_FILE, 'r') as f:
                creds = json.load(f)
                return creds.get('client_email', 'the service account email')
        except:
            return "your service account email"

    
    def get_sheet_data(self, credentials: Credentials, spreadsheet_id: str, 
                      range_name: str = "Sheet1!A:Z") -> List[List[str]]:
        """Get data from a specific range in the spreadsheet"""
        try:
            service = self.get_sheets_service(credentials)
            result = service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            
            return result.get('values', [])
        except HttpError as e:
            logger.error(f"Failed to get sheet data: {e}")
            raise
    
    def get_sheet_title_by_gid(self, spreadsheet_id: str, gid: int) -> Optional[str]:
        """Get sheet title by grid ID (gid)"""
        try:
            service = self.get_service()
            spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            
            for sheet in spreadsheet.get('sheets', []):
                sheet_props = sheet.get('properties', {})
                if sheet_props.get('sheetId') == gid:
                    return sheet_props.get('title')
            return None
        except Exception as e:
            logger.error(f"Failed to resolve GID {gid} for spreadsheet {spreadsheet_id}: {e}")
            retur    # Simple in-memory cache to prevent rate limiting (Cache for 30 seconds)
    _sheet_cache = {}
    
    def get_sheet_data_with_headers(self, spreadsheet_id: str,
                                   worksheet_name: str = "Sheet1", credentials=None) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Get sheet data as list of dictionaries with headers using Service Account (with caching)"""
        
        # 🔥 INITIALIZE Worksheet Name early for fallback access
        final_worksheet_name = worksheet_name.strip() if worksheet_name else "Sheet1"
        final_worksheet_name = final_worksheet_name.strip("'\"")

        # 1. 🕒 CHECK CACHE FIRST (Prevents slamming Google API with 25 concurrent requests)
        cache_key = f"{spreadsheet_id}:{final_worksheet_name}"
        current_time = datetime.now()
        
        if cache_key in self._sheet_cache:
            data, headers, expiry = self._sheet_cache[cache_key]
            if current_time < expiry:
                # logger.info(f"💾 Using cached data for spreadsheet {spreadsheet_id}")
                return data, headers
        
        response = None  # Initialize response for proper cleanup
        try:
            service = self.get_service()
            
            # 2. 🔥 DYNAMIC WORKSHEET SELECTION: If blank or 'Sheet1', try to find the actual first sheet
            final_worksheet_name = worksheet_name.strip() if worksheet_name else ""
            final_worksheet_name = final_worksheet_name.strip("'\"")

            if not final_worksheet_name or final_worksheet_name == "Sheet1":
                try:
                    available_sheets = self.get_available_sheets(None, spreadsheet_id)
                    if available_sheets:
                        # If 'Sheet1' was requested but doesn't exist, use the first one
                        if final_worksheet_name == "Sheet1" and "Sheet1" not in available_sheets:
                            final_worksheet_name = available_sheets[0]
                        elif not final_worksheet_name:
                            final_worksheet_name = available_sheets[0]
                    
                    if not final_worksheet_name:
                        final_worksheet_name = "Sheet1" # Final fallback
                except Exception as e:
                    logger.warning(f"Could not fetch available sheets, falling back to default: {e}")
                    if not final_worksheet_name:
                        final_worksheet_name = "Sheet1"
            
            # Construct range
            if any(char in final_worksheet_name for char in [' ', "'", '"', '!']):
                range_name = f"'{final_worksheet_name}'!A:Z"
            else:
                range_name = f"{final_worksheet_name}!A:Z"
            
            logger.info(f"🌐 Fetching FRESH data from Google Sheets: {spreadsheet_id}, range: {range_name}")
            
            # Use request directly for speed/stability on Windows
            import requests
            from google.auth.transport.requests import Request
            
            creds = self.get_service_account_credentials()
            if not creds:
                raise Exception("No credentials available")
            
            creds.refresh(Request())
            token = creds.token
            
            # Disable SSL verification to bypass Windows TLS hang (optional but used previously)
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{range_name}"
            api_res = requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=15, verify=False)
            
            if api_res.status_code != 200:
                raise Exception(f"Google API Error: {api_res.text}")
            
            response = api_res.json()
            values = response.get('values', [])
            
            if not values:
                return [], []
            
            # Normalize headers
            raw_headers = values[0]
            headers = []
            for i, header in enumerate(raw_headers):
                if header:
                    clean_header = str(header).strip()
                    if clean_header:
                        final_header = clean_header
                        counter = 1
                        while final_header in headers:
                            final_header = f"{clean_header}_{counter}"
                            counter += 1
                        headers.append(final_header)
                    else:
                        headers.append(f"column_{i+1}")
                else:
                    headers.append(f"column_{i+1}")
            
            # Construct data structure with row numbers (Nesting required by automation service)
            row_results = []
            for i, row in enumerate(values[1:]):
                # 🚀 SKIP BLANK ROWS: Only add if at least one cell has ACTUAL content
                # Note: Avoid str(cell) with None because it becomes "None" string
                if not any(cell is not None and str(cell).strip() != "" for cell in row):
                    continue
                    
                row_dict = {}
                row_num = i + 2 # Header is row 1
                for j, header in enumerate(headers):
                    if j < len(row):
                        row_dict[header] = row[j]
                    else:
                        row_dict[header] = ""
                row_results.append({'row_number': row_num, 'data': row_dict})
            
            # 🕒 10-SECOND CACHE: Extended to prevent rate limits and system lag
            self._sheet_cache[cache_key] = (row_results, headers, current_time + timedelta(seconds=10))
            
            logger.info(f"✅ Fetched {len(row_results)} rows from {spreadsheet_id} (Cached for 10s)")
            return row_results, headers
            
        except Exception as e:
            # 🔥 SILENT FALLBACK: If we know we are in public mode, don't spam warnings
            if not getattr(self, 'has_real_credentials', False):
                 # logger.debug(f"Public fallback fetch initiated for {spreadsheet_id}")
                 pass
            else:
                 logger.warning(f"⚠️  Credential-based fetch failed, trying PUBLIC FALLBACK: {e}")
            
            # 🔥 PUBLIC FALLBACK MODE (CSV Export)
            # This works if the sheet is shared as "Anyone with the link can view"
            try:
                import csv
                import io
                import requests
                import urllib.parse
                
                # Construct export URL using the Visualization API which supports ?sheet=NAME
                safe_sheet_name = urllib.parse.quote(final_worksheet_name)
                export_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/gviz/tq?tqx=out:csv&sheet={safe_sheet_name}"
                
                logger.info(f"🌐 Attempting Public Data Export (gviz): {export_url}")
                csv_res = requests.get(export_url, timeout=15)
                
                if csv_res.status_code != 200:
                    if "placeholder" in str(e).lower() or "credentials" in str(e).lower():
                        raise Exception("Google Sheets credentials are not set up AND the sheet is not Public. Please follow GOOGLE_SERVICE_ACCOUNT_SETUP.md OR share your sheet as 'Anyone with the link can view'.")
                    else:
                        raise e
                
                # Parse CSV
                content = csv_res.content.decode('utf-8')
                csv_reader = csv.reader(io.StringIO(content))
                values = list(csv_reader)
                
                if not values:
                    return [], []
                    
                # 🧠 STRICT COLUMN FILTER: Only include columns that have an EXPLICIT HEADER
                raw_headers = values[0]
                active_indices = []
                headers = []
                
                # Identify only columns with names (ignore ghost columns completely)
                for j, header in enumerate(raw_headers):
                    header_str = str(header).strip()
                    if header_str:
                        active_indices.append(j)
                        headers.append(header_str)
                
                # Fallback: if no headers found at all, use all columns with data
                if not headers:
                    for j, header in enumerate(raw_headers):
                        has_data = any(len(row) > j and str(row[j]).strip() != "" for row in values[1:])
                        if has_data:
                            active_indices.append(j)
                            headers.append(str(header).strip() if str(header).strip() else f"column_{j+1}")

                # Construct data structure using ONLY active columns
                row_results = []
                for i, row in enumerate(values[1:]):
                    # Skip completely empty rows
                    if not any(cell and str(cell).strip() != "" for cell in row):
                        continue
                        
                    row_dict = {}
                    row_num = i + 2
                    for k, col_idx in enumerate(active_indices):
                        header_name = headers[k]
                        row_dict[header_name] = row[col_idx] if col_idx < len(row) else ""
                    
                    row_results.append({'row_number': row_num, 'data': row_dict})
                
                logger.info(f"✨ Public Fallback Success: Fetched {len(row_results)} rows and {len(headers)} NAMED columns.")
                return row_results, headers
                
            except Exception as public_e:
                logger.error(f"❌ Public Fallback failed too: {public_e}")
                # Re-raise the original credential error if public fallback also fails
                if "placeholder" in str(e).lower():
                    raise Exception("Google Sheets credentials are not set up. Please update credentials/google-service-account.json with your real Service Account key OR share your sheet as 'Anyone with the link can view'.")
                raise e
        finally:
            # Clean up response if it exists
            if response is not None:
                try:
                    # No explicit close needed for Google API client, but good practice
                    pass
                except:
                    pass
    
    def validate_phone_number(self, phone: str) -> Optional[str]:
        """Validate and format phone number using unified normalizer"""
        return normalize_phone(phone)
    
    def process_message_template(self, template: str, row_data: Dict[str, Any]) -> str:
        """Process message template with row data using render_template utility"""
        return render_template(template, row_data)
    
    def extract_column_letter(self, column_name: str, headers: List[str]) -> Optional[str]:
        """Find column letter for a given column name"""
        try:
            if column_name in headers:
                index = headers.index(column_name)
                # Convert index to column letter (A, B, C, ..., AA, AB, etc.)
                column_letter = ''
                while index >= 0:
                    column_letter = chr(65 + (index % 26)) + column_letter
                    index = index // 26 - 1
                return column_letter
            return None
        except Exception as e:
            logger.error(f"Failed to extract column letter: {e}")
            return None
    
    def get_rows_by_criteria(self, credentials: Credentials, spreadsheet_id: str,
                           worksheet_name: str, trigger_type: TriggerType,
                           trigger_column: Optional[str] = None,
                           trigger_value: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get rows based on trigger criteria"""
        try:
            rows, headers = self.get_sheet_data_with_headers(credentials, spreadsheet_id, worksheet_name)
            
            if trigger_type == TriggerType.NEW_ROW:
                # For new row trigger, return all rows (implementation will track last processed row)
                return rows
            
            elif trigger_type == TriggerType.UPDATE_ROW:
                if not trigger_column or not trigger_value:
                    return rows
                
                # Filter rows where trigger column matches trigger value
                filtered_rows = []
                for row in rows:
                    column_value = row['data'].get(trigger_column, '')
                    if str(column_value).lower() == str(trigger_value).lower():
                        filtered_rows.append(row)
                
                return filtered_rows
            
            return rows
            
        except Exception as e:
            logger.error(f"Failed to get rows by criteria: {e}")
            return []
    
    def create_webhook_watch(self, credentials: Credentials, spreadsheet_id: str,
                           webhook_url: str) -> Optional[Dict[str, Any]]:
        """Create webhook watch for spreadsheet changes"""
        try:
            # This requires Google Drive API and Channels API
            # Implementation would depend on your webhook infrastructure
            logger.info(f"Webhook watch requested for spreadsheet {spreadsheet_id}")
            # TODO: Implement webhook creation using Drive API
            return None
        except Exception as e:
            logger.error(f"Failed to create webhook watch: {e}")
            return None
    
    def stop_webhook_watch(self, credentials: Credentials, channel_id: str, 
                          resource_id: str) -> bool:
        """Stop webhook watch"""
        try:
            # TODO: Implement webhook stop using Channels API
            logger.info(f"Webhook watch stopped for channel {channel_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to stop webhook watch: {e}")
            return False

    def update_cell(self, spreadsheet_id: str, worksheet_name: str, 
                   row_number: int, column_name: str, value: Any, headers: Optional[List[str]] = None) -> bool:
        """
        Update a specific cell in the Google Sheet.
        Column name is converted to letter (e.g., "Status" -> "D").
        If headers are provided, skips fetching sheet data.
        """
        # Added retry logic for flaky Google API updates
        max_retries = 3
        
        # 🔥 DYNAMIC WORKSHEET RESOLUTION: If blank or 'Sheet1', try to find the actual first sheet
        # This matches the fetching logic in get_sheet_data_with_headers
        final_worksheet = worksheet_name.strip() if worksheet_name else ""
        final_worksheet = final_worksheet.strip("'\"")
        
        if not final_worksheet or final_worksheet == "Sheet1":
            try:
                available = self.get_available_sheets(None, spreadsheet_id)
                if available:
                    if final_worksheet == "Sheet1" and "Sheet1" not in available:
                        final_worksheet = available[0]
                    elif not final_worksheet:
                        final_worksheet = available[0]
                if not final_worksheet: final_worksheet = "Sheet1"
            except:
                if not final_worksheet: final_worksheet = "Sheet1"
        
        worksheet_name = final_worksheet # Update variable for downstream use
        
        for attempt in range(max_retries):
            try:
                # 1. Get or use headers to find column index
                if not headers:
                    _, headers = self.get_sheet_data_with_headers(spreadsheet_id, worksheet_name)
                
                # Normalize column name for search
                target_col_lower = column_name.strip().lower()
                
                # Find the actual header name in the list (case-insensitive search)
                actual_header = None
                for h in headers:
                    if h.strip().lower() == target_col_lower:
                        actual_header = h
                        break
                
                if not actual_header:
                    logger.error(f"Column '{column_name}' not found in sheet. Available: {headers}")
                    return False
                    
                # 2. Get column letter using the ACTUAL header case
                col_letter = self.extract_column_letter(actual_header, headers)
                if not col_letter:
                     logger.error(f"Could not determine letter for column '{column_name}'")
                     return False
                     
                # 3. Construct A1 notation range (e.g., "Sheet1!D5")
                range_name = f"'{worksheet_name}'!{col_letter}{row_number}"
                
                # 4. Prepare value
                body = {
                    'values': [[value]]
                }
                
                # 5. Call API
                service = self.get_service()
                result = service.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id,
                    range=range_name,
                    valueInputOption="USER_ENTERED",
                    body=body
                ).execute()
                
                # 🔥 CRITICAL: Clear cache to ensure next fetch gets the updated status
                cache_key = f"{spreadsheet_id}:{worksheet_name}"
                if cache_key in self._sheet_cache:
                    del self._sheet_cache[cache_key]
                    logger.info(f"💾 Cache cleared for {spreadsheet_id} after update")

                logger.info(f"📝 Updated cell {range_name} to '{value}'. Updated cells: {result.get('updatedCells')}")
                return True
                
            except Exception as e:
                logger.warning(f"⚠️  Attempt {attempt + 1} failed to update cell: {e}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(2)
                    # Clear headers to force refresh on next attempt
                    headers = None
                else:
                    logger.error(f"❌ Final attempt failed to update cell: {e}")
                    return False
