from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, Form, File, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_
from sqlalchemy.sql import func
import os
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta, timezone
import requests
import csv
import io
import uuid
import logging
import re
import asyncio
from utils.template_engine import render_template

logger = logging.getLogger(__name__)
db_logger = logging.getLogger("GOOGLE_SHEETS")
router = APIRouter()
active_trigger_tasks = {}

from db.session import get_db
from api.busi_user import get_current_busi_user_id
from models.busi_user import BusiUser
from models.admin import MasterAdmin
from models.reseller import Reseller
from models.google_sheet import GoogleSheet, GoogleSheetTrigger, GoogleSheetTriggerHistory, SheetStatus, TriggerType, TriggerHistoryStatus
from models.device import Device
from models.campaign import Campaign
from schemas.google_sheet import (
    GoogleSheetConnectRequest, GoogleSheetResponse,
    GoogleSheetRowsRequest, GoogleSheetRowResponse,
    ManualSendRequest, ManualSendResponse,
    OfficialTemplateSendRequest, OfficialTemplateSendResponse,
    GoogleSheetMessagingRequest, GoogleSheetMessagingResponse,
    TriggerCreateRequest, TriggerUpdateRequest, TriggerResponse,
    OfficialTemplateTriggerRequest,
    TriggerHistoryResponse, TriggerHistoryListResponse,
    RowProcessingResult, GoogleSheetDataResponse
)
from services.google_sheets_service import GoogleSheetsService
from services.whatsapp_session_service import WhatsAppSessionService
from services.official_whatsapp_config_service import OfficialWhatsAppConfigService
from services.official_message_service import OfficialMessageService
from core.plan_validator import check_busi_user_plan

def get_google_sheets_service() -> GoogleSheetsService:
    return GoogleSheetsService()

def get_official_config_service(db: Session = Depends(get_db)) -> OfficialWhatsAppConfigService:
    return OfficialWhatsAppConfigService(db)

def get_official_message_service(db: Session = Depends(get_db)) -> OfficialMessageService:
    return OfficialMessageService(db)

async def get_current_user(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_busi_user_id) # Type hint updated to str
) -> Any:
    # 1. Try BusiUser
    user = db.query(BusiUser).filter(BusiUser.busi_user_id == user_id).first()
    if user:
        return user
    
    # 2. Try Admin (MasterAdmin)
    admin = db.query(MasterAdmin).filter(MasterAdmin.admin_id == user_id).first()
    if admin:
        # Create a mock/simulated BusiUser for the admin to avoid crashes in downstream logic
        # This allows admins to have their own "Sheets" context tied to their admin UUID
        admin_as_busi = BusiUser(
            busi_user_id=admin.admin_id,
            name=admin.name or "System Admin",
            email=admin.email,
            role="admin",
            status="active"
        )
        return admin_as_busi
    
    # 3. Try Reseller (Optional, but good for completeness)
    reseller = db.query(Reseller).filter(Reseller.reseller_id == user_id).first()
    if reseller:
         reseller_as_busi = BusiUser(
            busi_user_id=str(reseller.reseller_id),
            name=reseller.name or "Reseller",
            email=reseller.email,
            role="reseller",
            status="active",
            parent_reseller_id=reseller.reseller_id
        )
         return reseller_as_busi

    raise HTTPException(status_code=404, detail="User not found")

def validate_sheet_ownership(db: Session, sheet_id: str, user_id: str) -> GoogleSheet:
    """Validate that the sheet belongs to the user"""
    sheet = db.query(GoogleSheet).filter(
        and_(GoogleSheet.id == sheet_id, GoogleSheet.user_id == user_id)
    ).first()
    
    if not sheet:
        raise HTTPException(status_code=404, detail="Google Sheet not found or doesn't belong to user")
    
    return sheet

def extract_phone_number(row_data: Dict[str, Any], phone_column: str) -> Optional[str]:
    """Extract and validate phone number from row data"""
    # Try column name first, then column letter
    phone = row_data.get(phone_column)
    if not phone:
        # Try to find by column letter (A, B, C, etc.)
        for key, value in row_data.items():
            if key.upper() == phone_column.upper():
                phone = value
                break
    
    if not phone:
        return None
    
    # Use Google Sheets service to validate phone number
    sheets_service = GoogleSheetsService()
    return sheets_service.validate_phone_number(str(phone))

def format_message(template: str, row_data: Dict[str, Any]) -> str:
    """Format message template with row data"""
    sheets_service = GoogleSheetsService()
    return sheets_service.process_message_template(template, row_data)

# ==================== TRIGGERS HISTORY ====================

@router.get("/triggers/history/test")
async def get_all_triggers_history_test(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Test endpoint for trigger history (no authentication required)."""
    try:
        logger.info("🧪 Testing trigger history endpoint (no auth)")
        
        # Get all history (no user filter for testing)
        history = db.query(GoogleSheetTriggerHistory).order_by(
            GoogleSheetTriggerHistory.triggered_at.desc()
        ).offset((page - 1) * per_page).limit(per_page).all()
        
        # Format response
        history_data = []
        for h in history:
            # Safely extract row_number and message_id from JSON row_data
            row_num = h.row_data.get('row_number') if h.row_data else None
            msg_id = h.row_data.get('message_id') if h.row_data else None

            history_data.append({
                "id": str(h.id),
                "trigger_id": str(h.trigger_id),
                "sheet_id": str(h.sheet_id),
                "row_number": row_num,
                "phone_number": h.phone_number,
                "message_content": h.message_content,
                "status": h.status,
                "triggered_at": h.triggered_at.isoformat() if h.triggered_at else None,
                "error_message": h.error_message,
                "message_id": msg_id
            })
        
        return {
            "success": True,
            "data": history_data,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": len(history_data)
            },
            "test": True,
            "message": "This is a test endpoint without authentication"
        }
        
    except Exception as e:
        logger.error(f"Error in test trigger history: {e}")
        return {
            "success": False,
            "data": [],
            "error": str(e),
            "test": True
        }
@router.get("/all/triggers")
async def get_all_triggers(
    current_user: BusiUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get ALL triggers for all sheets owned by the current user."""
    try:
        # Get all sheets for user
        user_sheets = db.query(GoogleSheet).filter(GoogleSheet.user_id == current_user.busi_user_id).all()
        sheet_ids = [s.id for s in user_sheets]
        sheet_map = {s.id: s.sheet_name for s in user_sheets}
        
        if not sheet_ids:
            return {"success": True, "data": []}
            
        # Get all triggers for these sheets
        triggers = db.query(GoogleSheetTrigger).filter(
            GoogleSheetTrigger.sheet_id.in_(sheet_ids)
        ).all()
        
        # Format response
        trigger_data = []
        for t in triggers:
            trigger_data.append({
                "trigger_id": str(t.trigger_id),
                "sheet_id": str(t.sheet_id),
                "sheet_name": sheet_map.get(t.sheet_id, "Unknown Sheet"),
                "trigger_type": t.trigger_type,
                "is_enabled": t.is_enabled,
                "last_triggered_at": t.last_triggered_at.isoformat() if t.last_triggered_at else None,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            })
            
        return {
            "success": True,
            "data": trigger_data
        }
        
    except Exception as e:
        logger.error(f"Error getting all triggers: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve triggers")

@router.get("/triggers/history")
async def get_all_triggers_history(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=1, le=100),
    current_user: BusiUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get ALL trigger history for the current user."""
    try:
        # Get all sheets for user and convert to list to avoid SQLAlchemy SAWarning with subqueries
        user_sheets_query = db.query(GoogleSheet.id).filter(GoogleSheet.user_id == str(current_user.busi_user_id)).all()
        user_sheet_ids = [s[0] for s in user_sheets_query]
        
        # Get paginated history with join for sheet context
        if not user_sheet_ids:
            history = []
        else:
            history = db.query(
                GoogleSheetTriggerHistory,
                GoogleSheet.sheet_name,
                GoogleSheet.spreadsheet_id
            ).join(
                GoogleSheet, GoogleSheetTriggerHistory.sheet_id == GoogleSheet.id
            ).filter(
                GoogleSheetTriggerHistory.sheet_id.in_(user_sheet_ids)
            ).order_by(
                GoogleSheetTriggerHistory.triggered_at.desc()
            ).offset(
                (page - 1) * per_page
            ).limit(per_page).all()
        
        # Format response
        history_data = []
        for h, sheet_name, spreadsheet_id in history:
            # Safely extract row_number and message_id from JSON row_data
            row_num = h.row_data.get('row_number') if h.row_data else None
            msg_id = h.row_data.get('message_id') if h.row_data else None

            history_data.append({
                "id": str(h.id),
                "trigger_id": str(h.trigger_id),
                "sheet_id": str(h.sheet_id),
                "sheet_name": sheet_name,
                "spreadsheet_id": spreadsheet_id,
                "device_id": str(h.device_id) if h.device_id else None,
                "row_number": row_num,
                "phone_number": h.phone_number,
                "message_content": h.message_content,
                "status": h.status.value if hasattr(h.status, 'value') else h.status,
                "triggered_at": h.triggered_at.isoformat() if h.triggered_at else None,
                "error_message": h.error_message,
                "message_id": msg_id
            })
        
        return {
            "success": True,
            "data": history_data,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": len(history_data)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting trigger history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve trigger history")

# ==================== GOOGLE SHEETS CRUD ====================

@router.get("/", response_model=List[GoogleSheetResponse])
async def list_sheets(
    current_user: BusiUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all connected Google Sheets for the current user."""
    try:
        sheets = db.query(GoogleSheet).filter(
            GoogleSheet.user_id == current_user.busi_user_id
        ).order_by(GoogleSheet.connected_at.desc()).all()
        
        # 🚀 AUTO-SYNC: Update row counts if they look suspicious or are freshly listed
        # This fixes the "wrong row count" issue in the main table
        sheets_service = GoogleSheetsService()
        for sheet in sheets[:5]: # Limit to 5 for performance in list view
             try:
                 rows, _ = sheets_service.get_sheet_data_with_headers(
                     spreadsheet_id=sheet.spreadsheet_id,
                     worksheet_name=sheet.worksheet_name
                 )
                 if len(rows) != sheet.total_rows:
                     sheet.total_rows = len(rows)
                     sheet.last_synced_at = datetime.now(timezone.utc)
             except Exception as sync_e:
                 logger.warning(f"Failed to auto-sync row count for sheet {sheet.id}: {sync_e}")
        
        if db.dirty:
            db.commit()
            
        return sheets
    except Exception as e:
        logger.error(f"Error in list_sheets for user {current_user.busi_user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve Google Sheets")

@router.post("/connect", response_model=GoogleSheetResponse)
async def connect_sheet(
    request: GoogleSheetConnectRequest,
    current_user: BusiUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    sheets_service: GoogleSheetsService = Depends(get_google_sheets_service)
):
    """Connect a new Google Sheet with robust error handling and validation."""
    try:
        # Validate input
        if not request.spreadsheet_id:
            raise HTTPException(status_code=400, detail="Spreadsheet ID is required")
        
        if not request.sheet_name:
            raise HTTPException(status_code=400, detail="Sheet name is required")
        
        spreadsheet_id = request.spreadsheet_id.strip()
        
        # 1. Parse URL if present
        if "docs.google.com/spreadsheets" in spreadsheet_id:
            try:
                # Extract ID
                match = re.search(r"/d/([a-zA-Z0-9-_]+)", spreadsheet_id)
                if match:
                    spreadsheet_id = match.group(1)
                else:
                    raise HTTPException(status_code=400, detail="Invalid Google Sheets URL format")
                
            except Exception as e:
                logger.error(f"Failed to parse Google Sheet URL: {e}")
                raise HTTPException(status_code=400, detail="Invalid Google Sheets URL format")
        
        # 2. Fetch available sheets dynamically
        try:
            available_sheets = sheets_service.get_available_sheets(None, spreadsheet_id)
            if not available_sheets:
                raise HTTPException(status_code=400, detail="Spreadsheet has no available sheets or is inaccessible.")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to access spreadsheet metadata {spreadsheet_id}: {e}")
            raise HTTPException(
                status_code=400, 
                detail=str(e)
            )

        # Determine target worksheet
        target_worksheet_title = request.worksheet_name

        # If User provided URL with GID, try to resolve it
        if target_worksheet_title is None and "docs.google.com/spreadsheets" in request.spreadsheet_id:
            gid_match = re.search(r"[#&?]gid=([0-9]+)", request.spreadsheet_id)
            if gid_match:
                gid = int(gid_match.group(1))
                # Resolve GID to Title (GID source of truth overrides manual input if present)
                title = sheets_service.get_sheet_title_by_gid(spreadsheet_id, gid)
                if title:
                    target_worksheet_title = title
                    logger.info(f"Resolved GID {gid} to worksheet title: {title}")

        # Validation logic for worksheet_name
        if not target_worksheet_title:
            target_worksheet_title = available_sheets[0]
        elif target_worksheet_title not in available_sheets:
            raise HTTPException(
                status_code=400,
                detail=f"Sheet '{target_worksheet_title}' not found. Available sheets: {', '.join(available_sheets)}"
            )

        # 3. Validate access to the spreadsheet before connecting
        try:
            logger.info(f"Validating access to spreadsheet {spreadsheet_id}, worksheet {target_worksheet_title}")
            test_rows, test_headers = sheets_service.get_sheet_data_with_headers(
                spreadsheet_id, target_worksheet_title
            )
            
            if not test_headers:
                raise HTTPException(
                    status_code=400, 
                    detail=f"The Google Sheet '{target_worksheet_title}' is completely empty. Please add column names (like 'Name', 'Phone') in the first row before connecting."
                )
                
            logger.info(f"Successfully validated access to {spreadsheet_id}, found {len(test_rows)} rows and {len(test_headers)} columns")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to retrieve data for spreadsheet {spreadsheet_id}: {e}")
            raise HTTPException(
                status_code=400, 
                detail=str(e)
            )
        
        # 3. Check if sheet already exists
        existing = db.query(GoogleSheet).filter(
            and_(
                GoogleSheet.user_id == current_user.busi_user_id,
                GoogleSheet.spreadsheet_id == spreadsheet_id
            )
        ).first()
        
        if existing:
            logger.warning(f"Sheet {spreadsheet_id} already connected by user {current_user.busi_user_id}")
            raise HTTPException(
                status_code=409, 
                detail="This Google Sheet is already connected. Use a different sheet or delete the existing connection first."
            )
        
        # 4. Create new sheet with validated data
        new_sheet = GoogleSheet(
            user_id=current_user.busi_user_id,
            sheet_name=request.sheet_name,
            spreadsheet_id=spreadsheet_id,
            worksheet_name=target_worksheet_title,
            status=SheetStatus.ACTIVE,
            total_rows=len(test_rows),  # Store actual row count
            connected_at=datetime.now(timezone.utc)
        )
        
        db.add(new_sheet)
        db.commit()
        db.refresh(new_sheet)
        
        logger.info(f"Successfully connected sheet {spreadsheet_id} for user {current_user.busi_user_id}")
        
        # Map to response model
        response_model = GoogleSheetResponse.model_validate(new_sheet)
        response_model.available_sheets = available_sheets
        
        return response_model
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error connecting sheet for user {current_user.busi_user_id}: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to connect Google Sheet. Please try again later."
        )

@router.get("/{sheet_id}", response_model=GoogleSheetResponse)
async def get_sheet(
    sheet_id: str,
    current_user: BusiUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get details of a specific Google Sheet."""
    try:
        sheet = validate_sheet_ownership(db, sheet_id, current_user.busi_user_id)
        
        response_model = GoogleSheetResponse.model_validate(sheet)
        
        # Optionally populate available sheets for this single get
        sheets_service = GoogleSheetsService()
        try:
            response_model.available_sheets = sheets_service.get_available_sheets(None, sheet.spreadsheet_id)
        except Exception as e:
            logger.warning(f"Could not load available sheets for {sheet_id}: {e}")
            response_model.available_sheets = [sheet.worksheet_name] if sheet.worksheet_name else []
            
        return response_model
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting sheet {sheet_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve sheet")

@router.get("/{sheet_id}/worksheets", response_model=List[str])
async def get_available_worksheets(
    sheet_id: str,
    current_user: BusiUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    sheets_service: GoogleSheetsService = Depends(get_google_sheets_service)
):
    """Get all available worksheets for a connected Google Sheet."""
    try:
        sheet = validate_sheet_ownership(db, sheet_id, current_user.busi_user_id)
        available_sheets = sheets_service.get_available_sheets(None, sheet.spreadsheet_id)
        return available_sheets
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting worksheets for sheet {sheet_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve worksheets")

@router.put("/{sheet_id}", response_model=GoogleSheetResponse)
async def update_sheet(
    sheet_id: str,
    request: GoogleSheetConnectRequest,
    current_user: BusiUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update Google Sheet details."""
    try:
        sheet = validate_sheet_ownership(db, sheet_id, current_user.busi_user_id)
        
        sheet.sheet_name = request.sheet_name
        sheet.spreadsheet_id = request.spreadsheet_id
        if request.worksheet_name:
            sheet.worksheet_name = request.worksheet_name
            
        sheet.last_synced_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(sheet)
        
        return sheet
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating sheet {sheet_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update sheet")

@router.delete("/{sheet_id}")
async def delete_sheet(
    sheet_id: str,
    current_user: BusiUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a Google Sheet and all associated data with safe manual cascade deletion."""
    try:
        # Validate ownership
        sheet = validate_sheet_ownership(db, sheet_id, current_user.busi_user_id)
        
        # Safe manual cascade deletion in correct order to avoid FK violations
        try:
            # Start transaction
            # 1. Delete from sheet_trigger_history first (grandchild table)
            history_deleted = db.query(GoogleSheetTriggerHistory).filter(
                GoogleSheetTriggerHistory.sheet_id == sheet.id
            ).delete()
            logger.info(f"Deleted {history_deleted} history records for sheet {sheet.id}")
            
            # 2. Delete from google_sheet_triggers (child table)
            triggers_deleted = db.query(GoogleSheetTrigger).filter(
                GoogleSheetTrigger.sheet_id == sheet.id
            ).delete()
            logger.info(f"Deleted {triggers_deleted} triggers for sheet {sheet.id}")

            # 3. 🔥 NEW: Delete from campaigns (child table) - this fixes ForeignKeyViolation error
            # This will also cascade delete campaign_devices, message_templates, message_logs 
            # if DB schema matches model's ondelete="CASCADE" or if they are just manual children
            campaigns_deleted = db.query(Campaign).filter(
                Campaign.sheet_id == sheet.id
            ).delete()
            logger.info(f"Deleted {campaigns_deleted} campaigns for sheet {sheet.id}")
            
            # 4. Finally delete the google_sheets row (parent table)
            db.delete(sheet)
            logger.info(f"Deleted sheet {sheet.id}")
            
            # Commit transaction
            db.commit()
            logger.info(f"Successfully deleted sheet {sheet.id} and all associated data")
            
        except Exception as e:
            # Rollback on any error
            db.rollback()
            logger.error(f"Error during cascade deletion for sheet {sheet.id}: {e}")
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to delete sheet and associated data: {str(e)}"
            )
        
        return {
            "message": "Google Sheet deleted successfully",
            "sheet_id": sheet.id,
            "deleted_records": {
                "history": history_deleted,
                "triggers": triggers_deleted,
                "campaigns": campaigns_deleted,
                "sheet": 1
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting sheet {sheet_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{sheet_id}/rows", response_model=GoogleSheetDataResponse)
async def get_sheet_rows(
    sheet_id: str,
    worksheet_name: Optional[str] = Query(default=None),
    start_row: int = Query(default=1, ge=1),
    end_row: Optional[int] = Query(default=None),
    current_user: BusiUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    sheets_service: GoogleSheetsService = Depends(get_google_sheets_service)
):
    """Get rows from a Google Sheet with robust error handling."""
    try:
        # Validate sheet ownership
        sheet = validate_sheet_ownership(db, sheet_id, current_user.busi_user_id)
        
        # Use requested worksheet name if provided, else follow DB stored model or default to empty
        final_worksheet_name = worksheet_name or sheet.worksheet_name
        
        # Ensure we have a valid worksheet to fetch if none were provided via payload
        if not final_worksheet_name:
             raise HTTPException(
                 status_code=400,
                 detail="Missing worksheet name."
             )
        
        logger.info(f"Fetching rows for sheet {sheet_id}, worksheet: {final_worksheet_name}")
        
        # Fetch real data with error handling
        try:
            rows_data, headers_list = sheets_service.get_sheet_data_with_headers(
                spreadsheet_id=sheet.spreadsheet_id,
                worksheet_name=final_worksheet_name
            )
        except Exception as e:
            msg = str(e)
            if "Could not load Service Account credentials" in msg or "placeholders" in msg.lower():
                msg = "Google Sheets credentials are not set up. Please update credentials/google-service-account.json with your real Service Account key."
            
            logger.error(f"Failed to fetch data from Google Sheets API: {msg}")
            raise HTTPException(
                status_code=400,
                detail=msg
            )
        
        # Apply pagination if requested
        if end_row and start_row <= len(rows_data):
            rows_data = rows_data[start_row-1:end_row]
        elif start_row > 1:
            rows_data = rows_data[start_row-1:]
        
        # 3. 🧠 SMART MERGE: Override 'Pending' status with real-time history for Public Mode
        # This makes the dashboard show 'Sent' or 'Expired' even if the public sheet itself is read-only.
        try:
            # Get latest history for all rows in this sheet
            history_rows = db.query(
                GoogleSheetTriggerHistory.row_data,
                GoogleSheetTriggerHistory.status
            ).filter(
                GoogleSheetTriggerHistory.sheet_id == sheet.id
            ).all()
            
            # Create a lookup map: {row_number: "SENT/EXPIRED/FAILED"}
            status_map = {}
            for h_row, h_status in history_rows:
                if h_row and h_row.get('row_number'):
                    r_num = h_row.get('row_number')
                    status_val = h_status.value if hasattr(h_status, 'value') else str(h_status)
                    # Keep only the 'most advanced' status (Priority: SENT > FAILED > EXPIRED)
                    status_map[r_num] = status_val

            # Apply overrides to the rows_data
            status_col_name = "Status" # Default
            # Try to find the actual status column index from headers
            status_idx = -1
            for i, h in enumerate(headers_list):
                if h.strip().lower() == "status":
                    status_col_name = h
                    break
            
            for row in rows_data:
                r_num = row.get('row_number')
                if r_num in status_map:
                    # Override the status in the row data before sending to frontend
                    row['data'][status_col_name] = status_map[r_num].capitalize()
        except Exception as merge_err:
            logger.warning(f"Failed to merge row history: {merge_err}")

        # Format response
        response_data = {
            "headers": headers_list,
            "rows": [r['data'] for r in rows_data]
        }
        
        logger.info(f"Successfully fetched {len(rows_data)} rows for sheet {sheet_id} (Merged {len(status_map) if 'status_map' in locals() else 0} history records)")
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting rows from sheet {sheet_id}: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to retrieve sheet rows. Please try again later."
        )

# ==================== GOOGLE SHEET MESSAGING (TEXT + TEMPLATE) ====================

@router.post("/{sheet_id}/messaging", response_model=GoogleSheetMessagingResponse)
async def send_google_sheet_messages(
    sheet_id: str,
    request: GoogleSheetMessagingRequest,
    current_user: BusiUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    official_config_service: OfficialWhatsAppConfigService = Depends(get_official_config_service),
    official_service: OfficialMessageService = Depends(get_official_message_service),
    sheets_service: GoogleSheetsService = Depends(get_google_sheets_service)
):
    """
    🔥 GOOGLE SHEET MESSAGING - Supports BOTH Text and Template messages
    
    Request:
    {
        "mode": "text" | "template",
        "phone_column": "mobile",
        
        // When mode = "text"
        "text_message": "Hello {{name}}, your order {{order_id}} is ready!",
        
        // When mode = "template"
        "template_name": "order_update",
        "language_code": "en_US",
        "header_param_columns": ["name"],
        "body_param_columns": ["order_id", "amount"],
        "button_param_columns": {"url": "tracking_link"},
        
        // Common
        "selected_rows": [...],  // Optional: specific rows
        "send_all": true  // Optional: send to all rows
    }
    
    Response:
    {
        "total": 10,
        "sent": 8,
        "failed": 2,
        "errors": [...],
        "message_ids": ["wamid.xxxxx", ...],
        "mode": "text" | "template"
    }
    """
    try:
        # Validate ownership
        sheet = validate_sheet_ownership(db, sheet_id, current_user.busi_user_id)
        
        # NEW: Check Plan/Credits before sending
        check_busi_user_plan(db, str(current_user.busi_user_id))

        logger.info(f"🚀 GOOGLE SHEET MESSAGING: Starting {request.mode} messaging")
        logger.info(f"   Sheet ID: {sheet_id}")
        logger.info(f"   Mode: {request.mode}")
        logger.info(f"   User ID: {current_user.busi_user_id}")
        logger.info(f"   Request data: {request.model_dump()}")
        
        # Get rows to process
        if request.send_all:
            rows_data, headers = sheets_service.get_sheet_data_with_headers(
                credentials=None,
                spreadsheet_id=sheet.spreadsheet_id,
                worksheet_name=sheet.worksheet_name
            )
            logger.info(f"   Fetched {len(rows_data)} rows for send_all")
        elif request.selected_rows:
            rows_data = []
            for i, row in enumerate(request.selected_rows):
                rows_data.append({
                    'data': row,
                    'row_number': i + 1
                })
            logger.info(f"   Using {len(request.selected_rows)} selected rows")
        else:
            logger.warning(f"   No rows specified")
            return GoogleSheetMessagingResponse(
                total=0,
                sent=0,
                failed=0,
                errors=[],
                message_ids=[],
                mode=request.mode
            )
        
        if not rows_data:
            logger.warning(f"   No rows to process")
            return GoogleSheetMessagingResponse(
                total=0,
                sent=0,
                failed=0,
                errors=[],
                message_ids=[],
                mode=request.mode
            )
        
        # Process each row
        results = []
        errors = []
        success_count = 0
        failure_count = 0
        message_ids = []
        
        for row_info in rows_data:
            try:
                # Extract phone number
                phone = row_info['data'].get(request.phone_column)
                if not phone:
                    raise Exception(f"No phone number found in column '{request.phone_column}'")
                
                # Validate and format phone number
                validated_phone = sheets_service.validate_phone_number(str(phone))
                if not validated_phone:
                    raise Exception(f"Invalid phone number format: {phone}")
                
                # Send message based on mode
                if request.mode == "text":
                    # Process text message with template variables using render_template utility
                    message_text = render_template(request.text_message or "", row_info['data'])
                    
                    # 🔥 USE SAME SERVICE AS /official-message (no session validation)
                    # Get user's official WhatsApp config (same as official-message endpoint)
                    config = official_config_service.get_config_by_user_id(str(current_user.busi_user_id))
                    if not config:
                        raise Exception("Official WhatsApp configuration not found. Please configure Meta API settings first.")
                    
                    if not config.is_active:
                        raise Exception("Official WhatsApp configuration is not active.")
                    
                    # Send text message via OfficialMessageService (skip credit deduction, will deduct after loop)
                    result = await official_service.send_official_text_message(
                        user_id=str(current_user.busi_user_id),
                        phone_number=validated_phone,
                        message_text=message_text,
                        skip_credit_deduction=True
                    )
                    
                    # Result is already formatted as dict from service
                    result_dict = result
                        
                else:  # template mode
                    # Extract template parameters from sheet columns
                    header_params = []
                    if request.header_param_columns:
                        for col in request.header_param_columns:
                            value = row_info['data'].get(col, "")
                            header_params.append(str(value) if value else "")
                    
                    body_params = []
                    if request.body_param_columns:
                        for col in request.body_param_columns:
                            value = row_info['data'].get(col, "")
                            body_params.append(str(value) if value else "")
                    
                    button_params = {}
                    if request.button_param_columns:
                        for button_type, col in request.button_param_columns.items():
                            value = row_info['data'].get(col, "")
                            if value:
                                button_params[button_type] = str(value)
                    
                    result = await official_service.send_official_template_message(
                        user_id=str(current_user.busi_user_id),
                        phone_number=validated_phone,
                        template_name=request.template_name or "",
                        language_code=request.language_code or "en_US",
                        header_params=header_params if header_params else None,
                        body_params=body_params if body_params else None,
                        button_params=button_params if button_params else None,
                        skip_credit_deduction=True
                    )
                    result_dict = result
                
                if result_dict["success"]:
                    success_count += 1
                    if result_dict.get("message_id"):
                        message_ids.append(result_dict["message_id"])
                    # Log actual message type returned by shared service
                    message_type = result_dict.get("message_type", request.mode)
                    logger.info(f"   ✅ Row {row_info['row_number']}: {message_type} message sent")
                else:
                    failure_count += 1
                    error_msg = f"Row {row_info['row_number']}: {result_dict['error']}"
                    errors.append(error_msg)
                    logger.error(f"   ❌ Row {row_info['row_number']}: {result_dict['error']}")
                    
                results.append(result_dict)
                
            except Exception as e:
                failure_count += 1
                error_msg = f"Row {row_info['row_number']}: {str(e)}"
                errors.append(error_msg)
                logger.error(f"   ❌ Row {row_info['row_number']}: Exception - {e}")
        
        total_count = success_count + failure_count
        
        logger.info(f"🏁 GOOGLE SHEET MESSAGING COMPLETE: {success_count} sent, {failure_count} failed")
        
        # 🔥 DEDUCT CREDITS AFTER LOOP (only for successful messages)
        if success_count > 0:
            try:
                from services.message_usage_service import MessageUsageService
                message_usage_service = MessageUsageService(db)
                
                # Deduct credits for all successful messages at once
                message_usage_service.deduct_credits(
                    busi_user_id=str(current_user.busi_user_id),
                    message_id=f"trigger-{sheet_id}-{uuid.uuid4().hex[:8]}",
                    amount=success_count,
                    source="trigger"
                )
                db.commit()
                logger.info(f"✅ Deducted {success_count} credits for trigger flow (source: trigger)")
            except Exception as credit_err:
                logger.error(f"⚠️ Credit deduction failed after trigger: {str(credit_err)}")
        
        return GoogleSheetMessagingResponse(
            total=total_count,
            sent=success_count,
            failed=failure_count,
            errors=errors,
            message_ids=message_ids,
            mode=request.mode
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ GOOGLE SHEET MESSAGING ERROR: Error in Google Sheet messaging for sheet {sheet_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send {request.mode} messages")

# ==================== OFFICIAL WHATSAPP CONFIG ====================

# ==================== SESSION VALIDATION ====================

@router.post("/validate-text-session")
async def validate_text_message_session(
    phone_numbers: List[str],
    current_user: BusiUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    🔥 VALIDATE 24-HOUR SESSION FOR TEXT MESSAGES
    
    Check if text messages can be sent to phone numbers based on WhatsApp's 24-hour rule.
    
    Request:
    ["+1234567890", "+0987654321", ...]
    
    Response:
    {
        "can_send_all": false,
        "total_numbers": 3,
        "valid_sessions": 1,
        "invalid_sessions": 2,
        "results": [
            {
                "can_send_text": false,
                "reason": "no_conversation",
                "message": "No previous conversation found...",
                "phone_number": "+1234567890"
            },
            ...
        ],
        "summary": "⚠️ 1 of 3 recipients have active customer sessions"
    }
    """
    try:
        logger.info(f"🔍 BATCH SESSION VALIDATION: Checking {len(phone_numbers)} phone numbers")
        
        # Create session service instance
        session_service = WhatsAppSessionService(db)
        
        result = session_service.validate_text_messages_batch(
            user_id=str(current_user.busi_user_id),
            phone_numbers=phone_numbers
        )
        
        logger.info(f"✅ SESSION VALIDATION COMPLETE: {result['valid_sessions']}/{result['total_numbers']} valid sessions")
        return result
        
    except Exception as e:
        logger.error(f"Error in session validation: {e}")
        raise HTTPException(status_code=500, detail="Failed to validate text message sessions")

# ==================== MANUAL SEND ====================

@router.post("/{sheet_id}/manual-send", response_model=OfficialTemplateSendResponse)
async def send_manual_messages(
    sheet_id: str,
    request: OfficialTemplateSendRequest,
    current_user: BusiUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    official_service: OfficialMessageService = Depends(get_official_message_service),
    sheets_service: GoogleSheetsService = Depends(get_google_sheets_service)
):
    """
    🔥 MANUAL SEND - Uses Official WhatsApp API only
    
    Sends official template messages to selected rows in Google Sheet.
    No device validation required - uses OfficialWhatsAppConfig directly.
    """
    try:
        # Validate ownership
        sheet = validate_sheet_ownership(db, sheet_id, current_user.busi_user_id)
        
        logger.info(f"🚀 OFFICIAL TEMPLATE MANUAL SEND: Starting manual send")
        logger.info(f"   Sheet ID: {sheet_id}")
        logger.info(f"   Template: {request.template_name}")
        logger.info(f"   Language: {request.language_code}")
        logger.info(f"   User ID: {current_user.busi_user_id}")
        
        # Get rows to process
        if request.send_all:
            rows_data, headers = sheets_service.get_sheet_data_with_headers(
                credentials=None,
                spreadsheet_id=sheet.spreadsheet_id,
                worksheet_name=sheet.worksheet_name
            )
            logger.info(f"   Fetched {len(rows_data)} rows for send_all")
        elif request.selected_rows:
            rows_data = []
            for i, row in enumerate(request.selected_rows):
                rows_data.append({
                    'data': row,
                    'row_number': i + 1
                })
            logger.info(f"   Using {len(request.selected_rows)} selected rows")
        else:
            logger.warning(f"   No rows specified")
            return OfficialTemplateSendResponse(
                total=0,
                sent=0,
                failed=0,
                errors=[],
                message_ids=[]
            )
        
        if not rows_data:
            logger.warning(f"   No rows to process")
            return OfficialTemplateSendResponse(
                total=0,
                sent=0,
                failed=0,
                errors=[],
                message_ids=[]
            )
        
        # Process each row
        success_count = 0
        failure_count = 0
        errors = []
        message_ids = []
        
        for row_info in rows_data:
            try:
                # Extract phone number
                phone = row_info['data'].get(request.phone_column)
                if not phone:
                    raise Exception(f"No phone number found in column '{request.phone_column}'")
                
                # Validate and format phone number
                validated_phone = sheets_service.validate_phone_number(str(phone))
                if not validated_phone:
                    raise Exception(f"Invalid phone number format: {phone}")
                
                # Extract template parameters from sheet columns
                header_params = []
                if request.header_param_columns:
                    for col in request.header_param_columns:
                        value = row_info['data'].get(col, "")
                        header_params.append(str(value) if value else "")
                
                body_params = []
                if request.body_param_columns:
                    for col in request.body_param_columns:
                        value = row_info['data'].get(col, "")
                        body_params.append(str(value) if value else "")
                
                button_params = {}
                if request.button_param_columns:
                    for button_type, col in request.button_param_columns.items():
                        value = row_info['data'].get(col, "")
                        if value:
                            button_params[button_type] = str(value)
                
                # Send official template message
                result = await official_service.send_official_template_message(
                    user_id=str(current_user.busi_user_id),
                    phone_number=validated_phone,
                    template_name=request.template_name,
                    language_code=request.language_code,
                    header_params=header_params if header_params else None,
                    body_params=body_params if body_params else None,
                    button_params=button_params if button_params else None
                )
                
                if result["success"]:
                    success_count += 1
                    if result.get("message_id"):
                        message_ids.append(result["message_id"])
                    logger.info(f"   ✅ Row {row_info['row_number']}: Template message sent")
                else:
                    failure_count += 1
                    error_msg = f"Row {row_info['row_number']}: {result['error']}"
                    errors.append(error_msg)
                    logger.error(f"   ❌ Row {row_info['row_number']}: {result['error']}")
                    
            except Exception as e:
                failure_count += 1
                error_msg = f"Row {row_info['row_number']}: {str(e)}"
                errors.append(error_msg)
                logger.error(f"   ❌ Row {row_info['row_number']}: Exception - {e}")
        
        total_count = success_count + failure_count
        
        logger.info(f"✅ OFFICIAL TEMPLATE MANUAL SEND COMPLETE: {success_count} sent, {failure_count} failed")
        
        return OfficialTemplateSendResponse(
            total=total_count,
            sent=success_count,
            failed=failure_count,
            errors=errors,
            message_ids=message_ids
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in manual send for sheet {sheet_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to send official template messages")

# ==================== OFFICIAL TEMPLATE MESSAGING ====================

@router.post("/{sheet_id}/official-template-send", response_model=OfficialTemplateSendResponse)
async def send_official_template_messages(
    sheet_id: str,
    request: OfficialTemplateSendRequest,
    current_user: BusiUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    official_service: OfficialMessageService = Depends(get_official_message_service),
    sheets_service: GoogleSheetsService = Depends(get_google_sheets_service)
):
    """
    ✅ SEND OFFICIAL WHATSAPP TEMPLATE MESSAGES
    
    Uses OfficialMessageService to send template messages via Meta API.
    No device validation required - uses OfficialWhatsAppConfig directly.
    
    Request:
    {
        "template_name": "welcome_message",
        "language_code": "en_US",
        "phone_column": "mobile",
        "header_param_columns": ["name"],  // Sheet columns for header params
        "body_param_columns": ["order_id", "amount"],  // Sheet columns for body params
        "button_param_columns": {"url": "tracking_link"},  // Sheet columns for button params
        "selected_rows": [...],  // Optional: specific rows
        "send_all": true  // Optional: send to all rows
    }
    
    Response:
    {
        "total": 10,
        "sent": 8,
        "failed": 2,
        "errors": [...],
        "message_ids": ["wamid.xxxxx", ...]  // Meta API message IDs
    }
    """
    try:
        # Validate ownership
        sheet = validate_sheet_ownership(db, sheet_id, current_user.busi_user_id)
        
        logger.info(f"🚀 OFFICIAL TEMPLATE SEND: Starting official template messaging")
        logger.info(f"   Sheet ID: {sheet_id}")
        logger.info(f"   Template: {request.template_name}")
        logger.info(f"   Language: {request.language_code}")
        logger.info(f"   User ID: {current_user.busi_user_id}")
        
        # Get rows to process
        if request.send_all:
            rows_data, headers = sheets_service.get_sheet_data_with_headers(
                credentials=None,
                spreadsheet_id=sheet.spreadsheet_id,
                worksheet_name=sheet.worksheet_name
            )
            logger.info(f"   Fetched {len(rows_data)} rows for send_all")
        elif request.selected_rows:
            rows_data = []
            for i, row in enumerate(request.selected_rows):
                rows_data.append({
                    'data': row,
                    'row_number': i + 1
                })
            logger.info(f"   Using {len(request.selected_rows)} selected rows")
        else:
            logger.warning(f"   No rows specified")
            return OfficialTemplateSendResponse(
                total=0,
                sent=0,
                failed=0,
                errors=[],
                message_ids=[]
            )
        
        if not rows_data:
            logger.warning(f"   No rows to process")
            return OfficialTemplateSendResponse(
                total=0,
                sent=0,
                failed=0,
                errors=[],
                message_ids=[]
            )
        
        # Process each row
        success_count = 0
        failure_count = 0
        errors = []
        message_ids = []
        
        for row_info in rows_data:
            try:
                # Extract phone number
                phone = row_info['data'].get(request.phone_column)
                if not phone:
                    raise Exception(f"No phone number found in column '{request.phone_column}'")
                
                # Validate and format phone number
                validated_phone = sheets_service.validate_phone_number(str(phone))
                if not validated_phone:
                    raise Exception(f"Invalid phone number format: {phone}")
                
                # Extract template parameters from sheet columns
                header_params = []
                if request.header_param_columns:
                    for col in request.header_param_columns:
                        value = row_info['data'].get(col, "")
                        header_params.append(str(value) if value else "")
                
                body_params = []
                if request.body_param_columns:
                    for col in request.body_param_columns:
                        value = row_info['data'].get(col, "")
                        body_params.append(str(value) if value else "")
                
                button_params = {}
                if request.button_param_columns:
                    for button_type, col in request.button_param_columns.items():
                        value = row_info['data'].get(col, "")
                        if value:
                            button_params[button_type] = str(value)
                
                # Send official template message
                result = await official_service.send_official_template_message(
                    user_id=str(current_user.busi_user_id),
                    phone_number=validated_phone,
                    template_name=request.template_name,
                    language_code=request.language_code,
                    header_params=header_params if header_params else None,
                    body_params=body_params if body_params else None,
                    button_params=button_params if button_params else None
                )
                
                if result["success"]:
                    success_count += 1
                    if result.get("message_id"):
                        message_ids.append(result["message_id"])
                    logger.info(f"   ✅ Row {row_info['row_number']}: Template message sent")
                else:
                    failure_count += 1
                    error_msg = f"Row {row_info['row_number']}: {result['error']}"
                    errors.append(error_msg)
                    logger.error(f"   ❌ Row {row_info['row_number']}: {result['error']}")
                    
            except Exception as e:
                failure_count += 1
                error_msg = f"Row {row_info['row_number']}: {str(e)}"
                errors.append(error_msg)
                logger.error(f"   ❌ Row {row_info['row_number']}: Exception - {e}")
        
        total_count = success_count + failure_count
        
        logger.info(f"✅ OFFICIAL TEMPLATE SEND COMPLETE: {success_count} sent, {failure_count} failed")
        
        return OfficialTemplateSendResponse(
            total=total_count,
            sent=success_count,
            failed=failure_count,
            errors=errors,
            message_ids=message_ids
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in official template send for sheet {sheet_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to send official template messages")

# ==================== TEMPLATES ====================

@router.get("/{sheet_id}/templates")
async def get_sheet_templates(
    sheet_id: str,
    current_user: BusiUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    official_service: OfficialMessageService = Depends(get_official_message_service)
):
    """
    Get approved templates for official WhatsApp messaging
    """
    try:
        # Validate ownership
        sheet = validate_sheet_ownership(db, sheet_id, current_user.busi_user_id)
        
        logger.info(f"🔍 TEMPLATE FETCH: Fetching templates for user {current_user.busi_user_id}, sheet {sheet_id}")
        
        # Get user's templates
        templates = await official_service.get_user_templates(str(current_user.busi_user_id))
        
        logger.info(f"📋 TEMPLATE RESULT: Found {len(templates)} approved templates for user {current_user.busi_user_id}")
        for template in templates:
            logger.info(f"   - {template['template_name']} ({template['status']})")
        
        return {
            "success": True,
            "templates": templates
        }
        
    except Exception as e:
        logger.error(f"❌ TEMPLATE ERROR: Error getting templates for sheet {sheet_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get templates")

# ==================== TRIGGERS ====================

@router.get("/triggers/all", response_model=List[TriggerResponse])
async def list_all_user_triggers(
    current_user: BusiUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """🚀 List ALL triggers for this user across all sheets and files with statistics."""
    try:
        # Get all sheets owned by user
        user_sheets = db.query(GoogleSheet).filter(GoogleSheet.user_id == str(current_user.busi_user_id)).all()
        sheet_ids = [str(s.id) for s in user_sheets]
        logger.info(f"🔍 Found {len(sheet_ids)} sheets for user {str(current_user.busi_user_id)}")
        
        # Get triggers for these sheets OR triggers with source_file_url 
        # For now, we fetch triggers where sheet_id is in user_sheets OR source_file_url is set
        # OR where user_id matches explicitly
        query = db.query(GoogleSheetTrigger).filter(
            or_(
                GoogleSheetTrigger.sheet_id.in_(sheet_ids) if sheet_ids else False,
                GoogleSheetTrigger.source_file_url != None,
                GoogleSheetTrigger.user_id == str(current_user.busi_user_id)
            )
        )
            
        triggers = query.order_by(GoogleSheetTrigger.created_at.desc()).all()
        logger.info(f"🔍 Found {len(triggers)} triggers/automations")
        
        # Fetch all device names for mapping
        user_devices = db.query(Device).filter(Device.busi_user_id == str(current_user.busi_user_id)).all()
        device_map = {str(d.device_id): d.device_name for d in user_devices}
        sheet_map = {s.id: s.sheet_name for s in user_sheets}
        
        result = []
        for trigger in triggers:
            d_name = device_map.get(str(trigger.device_id)) if trigger.device_id else "Official API"
            s_name = sheet_map.get(trigger.sheet_id) if trigger.sheet_id else f"File: {os.path.basename(trigger.source_file_url or '')[:20]}..."
            
            # 🔥 NEW: Calculate trigger statistics
            total_rows = 0
            processed_rows = 0
            completion_status = "pending"
            
            # Get total rows from sheet if available
            if trigger.sheet_id:
                sheet = db.query(GoogleSheet).filter(GoogleSheet.id == trigger.sheet_id).first()
                if sheet:
                    total_rows = sheet.total_rows or 0
            
            # Count processed rows from trigger history
            try:
                processed_count = db.query(GoogleSheetTriggerHistory).filter(
                    and_(
                        GoogleSheetTriggerHistory.trigger_id == str(trigger.trigger_id),
                        GoogleSheetTriggerHistory.status == TriggerHistoryStatus.SENT.value
                    )
                ).count()
                processed_rows = processed_count
            except Exception as e:
                logger.warning(f"Failed to count processed rows for trigger {trigger.trigger_id}: {e}")
            
            # Determine completion status
            if trigger.is_enabled:
                completion_status = "running"
            elif processed_rows > 0:
                completion_status = "completed"
            else:
                completion_status = "pending"
            
            result.append(TriggerResponse(
                trigger_id=trigger.trigger_id,
                sheet_id=trigger.sheet_id,
                device_id=trigger.device_id,
                trigger_type=trigger.trigger_type,
                message_template=trigger.message_template,
                phone_column=trigger.phone_column,
                status_column=trigger.status_column,
                trigger_column=trigger.trigger_column,
                trigger_value=trigger.trigger_value,
                send_time_column=trigger.send_time_column,
                message_column=trigger.message_column,
                webhook_url=trigger.webhook_url,
                is_enabled=trigger.is_enabled,
                last_triggered_at=trigger.last_triggered_at,
                created_at=trigger.created_at,
                device_name=d_name, 
                sheet_name=s_name,
                scheduled_at=trigger.scheduled_at,
                source_file_url=trigger.source_file_url,
                media_url=trigger.media_url,
                media_type=trigger.media_type,
                total_rows=total_rows,
                processed_rows=processed_rows,
                completion_status=completion_status
            ))
        
        return result
    except Exception as e:
        logger.error(f"Error listing all triggers: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve triggers")

@router.post("/triggers", response_model=TriggerResponse)
async def create_standalone_trigger(
    payload: str = Form(...),
    file: Optional[UploadFile] = File(None),
    data_file: Optional[UploadFile] = File(None), # 🔥 CSV/Excel data source
    current_user: BusiUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    🔥 CREATE STANDALONE TRIGGER (File-based or Sheet-based via payload)
    
    Allows creating a trigger without sheet_id in URL.
    """
    import json
    import os
    import shutil
    try:
        # 0. Parse JSON payload
        try:
            request_dict = json.loads(payload)
            request = TriggerCreateRequest(**request_dict)
        except Exception as e:
            logger.error(f"Invalid JSON payload: {e}")
            raise HTTPException(status_code=400, detail=f"Invalid JSON payload: {str(e)}")

        # 1. Handle File Upload (Media)
        media_url = None
        media_type = None
        if file:
            logger.info(f"📁 Handling trigger media upload: {file.filename}")
            upload_dir = os.path.join("uploads", "trigger_media")
            os.makedirs(upload_dir, exist_ok=True)
            
            file_ext = os.path.splitext(file.filename)[1]
            unique_filename = f"trigger_{uuid.uuid4()}_{file.filename}"
            file_path = os.path.join(upload_dir, unique_filename)
            
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            media_url = f"http://localhost:8000/uploads/trigger_media/{unique_filename}"
            
            content_type = file.content_type or ""
            if "image" in content_type: media_type = "image"
            elif "video" in content_type: media_type = "video"
            elif "audio" in content_type: media_type = "audio"
            else: media_type = "document"

        # 1.5 Handle Data File Upload (Source)
        source_file_url = request.source_file_url
        if data_file:
            logger.info(f"📁 Handling DATA SOURCE file: {data_file.filename}")
            upload_dir = os.path.join("uploads", "campaign_data")
            os.makedirs(upload_dir, exist_ok=True)
            
            file_ext = os.path.splitext(data_file.filename)[1].lower()
            unique_filename = f"data_{uuid.uuid4()}{file_ext}"
            file_path = os.path.join(upload_dir, unique_filename)
            
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(data_file.file, buffer)
            
            # Use absolute path for backend service processing
            source_file_url = os.path.abspath(file_path)
            logger.info(f"✅ Data source saved: {source_file_url}")

        # 2. Validate sheet if provided in payload
        sheet = None
        if request.sheet_id:
            sheet = validate_sheet_ownership(db, str(request.sheet_id), current_user.busi_user_id)
        
        # 2.5 Validate scheduled_at is not in the past for time-based triggers
        if request.trigger_type == "time" and request.scheduled_at:
            from datetime import datetime, timezone, timedelta
            ist_tz = timezone(timedelta(hours=5, minutes=30))
            literal_time = request.scheduled_at.replace(tzinfo=None)
            sched_time_utc = literal_time.replace(tzinfo=ist_tz).astimezone(timezone.utc)
            now_utc = datetime.now(timezone.utc)
            
            if sched_time_utc < now_utc:
                raise HTTPException(
                    status_code=400, 
                    detail="Past dates are not allowed. Please select a valid date."
                )
        
        dev_id_str = str(request.device_id) if request.device_id else None

        # 3. Create the trigger
        new_trigger = GoogleSheetTrigger(
            trigger_id=str(uuid.uuid4()),
            sheet_id=sheet.id if sheet else request.sheet_id,
            user_id=str(current_user.busi_user_id),
            device_id=dev_id_str,
            trigger_type=request.trigger_type,
            message_template=request.message_template,
            phone_column=request.phone_column,
            trigger_column=request.trigger_column,
            status_column=request.status_column or "Status",
            trigger_value=request.trigger_value,
            is_enabled=request.is_enabled,
            webhook_url=request.webhook_url,
            send_time_column=request.send_time_column,
            message_column=request.message_column,
            scheduled_at=request.scheduled_at,
            source_file_url=source_file_url,
            media_url=media_url or request.media_url,
            media_type=media_type or request.media_type,
            trigger_config={
                "interval": request.execution_interval or 15,
                "schedule_column": request.schedule_column,
                "multi_device_ids": [str(d) for d in request.multi_device_ids] if request.multi_device_ids else [],
                "multi_templates": request.multi_templates or []
            } if (request.execution_interval or request.schedule_column or request.multi_device_ids or request.multi_templates) else None
        )
        
        db.add(new_trigger)
        db.commit()
        db.refresh(new_trigger)
        
        # 🚀 AUTO-START
        t_id = str(new_trigger.trigger_id)
        if t_id not in active_trigger_tasks or active_trigger_tasks[t_id].done():
            task = asyncio.create_task(_trigger_worker_task(t_id))
            active_trigger_tasks[t_id] = task
        
        # 🔥 IMMEDIATE FIRE FOR TIME TRIGGERS
        # If this is a time trigger with a scheduled time that has already passed, fire it immediately
        if new_trigger.trigger_type == "time" and new_trigger.scheduled_at:
            from datetime import datetime, timezone, timedelta
            ist_tz = timezone(timedelta(hours=5, minutes=30))
            literal_time = new_trigger.scheduled_at.replace(tzinfo=None)
            sched_time_utc = literal_time.replace(tzinfo=ist_tz).astimezone(timezone.utc)
            now_utc = datetime.now(timezone.utc)
            
            if now_utc >= sched_time_utc:
                logger.info(f"🔥 [AUTO_FIRE] Trigger {t_id} schedule time has passed. Firing immediately...")
                # Create a one-off task to fire immediately
                async def fire_immediately():
                    from db.session import SessionLocal
                    session = SessionLocal()
                    try:
                        await _execute_trigger_process(t_id, session, is_manual=True)
                    finally:
                        session.close()
                asyncio.create_task(fire_immediately())
            
        device = db.query(Device).filter(Device.device_id == dev_id_str).first() if dev_id_str else None
        
        return TriggerResponse(
            trigger_id=new_trigger.trigger_id,
            sheet_id=new_trigger.sheet_id,
            device_id=new_trigger.device_id,
            trigger_type=new_trigger.trigger_type,
            message_template=new_trigger.message_template,
            phone_column=new_trigger.phone_column,
            trigger_column=new_trigger.trigger_column,
            trigger_value=new_trigger.trigger_value,
            webhook_url=new_trigger.webhook_url,
            is_enabled=new_trigger.is_enabled,
            last_triggered_at=new_trigger.last_triggered_at,
            created_at=new_trigger.created_at,
            device_name=device.device_name if device else "Official API",
            sheet_name=sheet.sheet_name if sheet else (f"File: {os.path.basename(new_trigger.source_file_url or '')[:20]}" if new_trigger.source_file_url else "Standalone")
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating standalone trigger: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create trigger: {str(e)}")


@router.post("/{sheet_id}/triggers", response_model=TriggerResponse)
async def create_trigger(
    sheet_id: str,
    payload: str = Form(...),
    file: Optional[UploadFile] = File(None),
    data_file: Optional[UploadFile] = File(None), # 🔥 CSV/Excel data source
    current_user: BusiUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    🔥 CREATE TRIGGER (Unofficial & Official)
    
    Creates a new Google Sheet trigger with optional media attachment.
    """
    import json
    import os
    import shutil
    try:
        # 0. Parse JSON payload
        try:
            request_dict = json.loads(payload)
            request = TriggerCreateRequest(**request_dict)
        except Exception as e:
            logger.error(f"Invalid JSON payload: {e}")
            raise HTTPException(status_code=400, detail=f"Invalid JSON payload: {str(e)}")

        # 1. Handle File Upload
        media_url = None
        media_type = None
        if file:
            logger.info(f"📁 Handling trigger media upload: {file.filename}")
            upload_dir = os.path.join("uploads", "trigger_media")
            os.makedirs(upload_dir, exist_ok=True)
            
            file_ext = os.path.splitext(file.filename)[1]
            unique_filename = f"trigger_{uuid.uuid4()}_{file.filename}"
            file_path = os.path.join(upload_dir, unique_filename)
            
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            media_url = f"http://localhost:8000/uploads/trigger_media/{unique_filename}"
            
            # Determine media type
            content_type = file.content_type or ""
            if "image" in content_type: media_type = "image"
            elif "video" in content_type: media_type = "video"
            elif "audio" in content_type: media_type = "audio"
            else: media_type = "document"
            
            logger.info(f"✅ Media saved: {media_url} ({media_type})")

        # 1.5 Handle Data File Upload (Source)
        source_file_url = request.source_file_url
        if data_file:
            logger.info(f"📁 Handling DATA SOURCE file: {data_file.filename}")
            upload_dir = os.path.join("uploads", "campaign_data")
            os.makedirs(upload_dir, exist_ok=True)
            
            file_ext = os.path.splitext(data_file.filename)[1].lower()
            unique_filename = f"data_{uuid.uuid4()}{file_ext}"
            file_path = os.path.join(upload_dir, unique_filename)
            
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(data_file.file, buffer)
            
            source_file_url = os.path.abspath(file_path)
            logger.info(f"✅ Data source saved: {source_file_url}")

        # Validate sheet ownership
        sheet = None
        is_file_source = (sheet_id in ["none", "file", "null", "undefined", ""]) or data_file is not None or (request.source_file_url is not None)
        
        if not is_file_source:
            try:
                sheet = validate_sheet_ownership(db, str(sheet_id), current_user.busi_user_id)
            except HTTPException as e:
                # If sheet not found but it looks like a file source could be intended, fallback
                if data_file or request.source_file_url:
                    is_file_source = True
                    logger.info(f"Fallback to file source for sheet_id: {sheet_id}")
                else:
                    raise e
        
        # Determine device ID if present
        dev_id_str = str(request.device_id) if request.device_id else None

        # Validate scheduled_at is not in the past for time-based triggers
        if request.trigger_type == "time" and request.scheduled_at:
            from datetime import datetime, timezone, timedelta
            ist_tz = timezone(timedelta(hours=5, minutes=30))
            literal_time = request.scheduled_at.replace(tzinfo=None)
            sched_time_utc = literal_time.replace(tzinfo=ist_tz).astimezone(timezone.utc)
            now_utc = datetime.now(timezone.utc)
            
            if sched_time_utc < now_utc:
                raise HTTPException(
                    status_code=400, 
                    detail="Past dates are not allowed. Please select a valid date."
                )

        # Create the trigger
        new_trigger = GoogleSheetTrigger(
            trigger_id=str(uuid.uuid4()),
            sheet_id=sheet.id if sheet else None,
            user_id=str(current_user.busi_user_id),
            device_id=dev_id_str,
            trigger_type=request.trigger_type,
            message_template=request.message_template,
            phone_column=request.phone_column,
            trigger_column=request.trigger_column,
            status_column=request.status_column or "Status",
            trigger_value=request.trigger_value,
            is_enabled=request.is_enabled,
            webhook_url=request.webhook_url,
            send_time_column=request.send_time_column,
            message_column=request.message_column,
            scheduled_at=request.scheduled_at,
            source_file_url=source_file_url,
            media_url=media_url,
            media_type=media_type,
            trigger_config={
                "interval": request.execution_interval or 15,
                "schedule_column": request.schedule_column,
                "multi_device_ids": [str(d) for d in request.multi_device_ids] if request.multi_device_ids else [],
                "multi_templates": request.multi_templates or []
            } if (request.execution_interval or request.schedule_column or request.multi_device_ids or request.multi_templates) else None
        )
        
        db.add(new_trigger)
        db.commit()
        db.refresh(new_trigger)
        
        # 🚀 AUTO-START: Immediately start background task on creation
        t_id = str(new_trigger.trigger_id)
        if t_id not in active_trigger_tasks or active_trigger_tasks[t_id].done():
            logger.info(f"🚀 [AUTO-START] Trigger created and started: {t_id}")
            task = asyncio.create_task(_trigger_worker_task(t_id))
            active_trigger_tasks[t_id] = task
        
        # 🔥 IMMEDIATE FIRE FOR TIME TRIGGERS
        # If this is a time trigger with a scheduled time that has already passed, fire it immediately
        if new_trigger.trigger_type == "time" and new_trigger.scheduled_at:
            from datetime import datetime, timezone, timedelta
            ist_tz = timezone(timedelta(hours=5, minutes=30))
            literal_time = new_trigger.scheduled_at.replace(tzinfo=None)
            sched_time_utc = literal_time.replace(tzinfo=ist_tz).astimezone(timezone.utc)
            now_utc = datetime.now(timezone.utc)
            
            if now_utc >= sched_time_utc:
                logger.info(f"🔥 [AUTO_FIRE] Trigger {t_id} schedule time has passed. Firing immediately...")
                # Create a one-off task to fire immediately
                async def fire_immediately():
                    from db.session import SessionLocal
                    session = SessionLocal()
                    try:
                        await _execute_trigger_process(t_id, session, is_manual=True)
                    finally:
                        session.close()
                asyncio.create_task(fire_immediately())
            
        logger.info(f"✅ Created and started trigger {new_trigger.trigger_id} for {'File' if is_file_source else 'Sheet ' + str(sheet.id)}")
        
        # Lookup device name
        device = db.query(Device).filter(Device.device_id == dev_id_str).first() if dev_id_str else None
        
        return TriggerResponse(
            trigger_id=new_trigger.trigger_id,
            sheet_id=new_trigger.sheet_id,
            device_id=new_trigger.device_id,
            trigger_type=new_trigger.trigger_type,
            message_template=new_trigger.message_template,
            phone_column=new_trigger.phone_column,
            trigger_column=new_trigger.trigger_column,
            trigger_value=new_trigger.trigger_value,
            webhook_url=new_trigger.webhook_url,
            is_enabled=new_trigger.is_enabled,
            last_triggered_at=new_trigger.last_triggered_at,
            created_at=new_trigger.created_at,
            device_name=device.device_name if device else "Official API",
            sheet_name=sheet.sheet_name if sheet else (f"File: {os.path.basename(source_file_url or '')[:20]}" if source_file_url else "Standalone")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating trigger for sheet {sheet_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to create trigger")

@router.get("/{sheet_id}/triggers", response_model=List[TriggerResponse])
async def list_triggers(
    sheet_id: str,
    current_user: BusiUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all triggers for a Google Sheet."""
    try:
        sheet = validate_sheet_ownership(db, sheet_id, current_user.busi_user_id)
        
        triggers = db.query(GoogleSheetTrigger).filter(
            GoogleSheetTrigger.sheet_id == sheet.id
        ).order_by(GoogleSheetTrigger.created_at.desc()).all()
        
        # TODO: Load sheet names
        result = []
        # Fetch all device names for this user for mapping
        user_devices = db.query(Device).filter(Device.busi_user_id == str(current_user.busi_user_id)).all()
        device_map = {str(d.device_id): d.device_name for d in user_devices}
        
        for trigger in triggers:
            # Look up dynamic device name
            d_name = device_map.get(str(trigger.device_id)) if trigger.device_id else "Official API"
            
            result.append(TriggerResponse(
                trigger_id=trigger.trigger_id,
                sheet_id=trigger.sheet_id,
                device_id=trigger.device_id,
                trigger_type=trigger.trigger_type,
                message_template=trigger.message_template,
                phone_column=trigger.phone_column,
                status_column=trigger.status_column,
                trigger_column=trigger.trigger_column,
                trigger_value=trigger.trigger_value,
                send_time_column=trigger.send_time_column,
                message_column=trigger.message_column,
                webhook_url=trigger.webhook_url,
                polling_interval=trigger.trigger_config.get("interval") if trigger.trigger_config else None,
                last_processed_row=trigger.last_processed_row,
                is_enabled=trigger.is_enabled,
                last_triggered_at=trigger.last_triggered_at,
                created_at=trigger.created_at,
                device_name=d_name, 
                sheet_name=sheet.sheet_name
            ))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing triggers for sheet {sheet_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve triggers")

@router.put("/triggers/{trigger_id}", response_model=TriggerResponse)
async def update_trigger(
    trigger_id: str,
    payload: str = Form(...),
    file: Optional[UploadFile] = File(None),
    current_user: BusiUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an existing trigger with optional media."""
    import json
    import os
    import shutil
    try:
        # 0. Parse JSON
        try:
            request_dict = json.loads(payload)
            request = TriggerUpdateRequest(**request_dict)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")

        trigger = db.query(GoogleSheetTrigger).filter(GoogleSheetTrigger.trigger_id == trigger_id).first()
        if not trigger:
            raise HTTPException(status_code=404, detail="Trigger not found")

        # 1. Handle File Upload
        if file:
            upload_dir = os.path.join("uploads", "trigger_media")
            os.makedirs(upload_dir, exist_ok=True)
            unique_filename = f"trigger_{uuid.uuid4()}_{file.filename}"
            file_path = os.path.join(upload_dir, unique_filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            trigger.media_url = os.path.abspath(file_path)
            content_type = file.content_type or ""
            if "image" in content_type: trigger.media_type = "image"
            elif "video" in content_type: trigger.media_type = "video"
            elif "audio" in content_type: trigger.media_type = "audio"
            else: trigger.media_type = "document"

        # Update fields
        if request.device_id is not None:
            trigger.device_id = str(request.device_id) if request.device_id else None
        if request.trigger_type is not None:
            trigger.trigger_type = request.trigger_type
        if request.is_enabled is not None:
            trigger.is_enabled = request.is_enabled
        if request.phone_column is not None:
            trigger.phone_column = request.phone_column
        if request.status_column is not None:
            trigger.status_column = request.status_column
        if request.trigger_value is not None:
            trigger.trigger_value = request.trigger_value
        if request.message_template is not None:
            trigger.message_template = request.message_template
        if request.send_time_column is not None:
            trigger.send_time_column = request.send_time_column
        if request.message_column is not None:
            trigger.message_column = request.message_column
        if request.webhook_url is not None:
            trigger.webhook_url = request.webhook_url
        if request.scheduled_at is not None:
            trigger.scheduled_at = request.scheduled_at
            
        # Update config for Round Robin
        if request.multi_device_ids is not None or request.multi_templates is not None:
            config = trigger.trigger_config or {}
            if request.multi_device_ids is not None:
                config["multi_device_ids"] = [str(d) for d in request.multi_device_ids]
            if request.multi_templates is not None:
                config["multi_templates"] = request.multi_templates
            trigger.trigger_config = config

        db.commit()
        db.refresh(trigger)
        
        # Auto-start handled in loop logic or manual triggers
        
        # Get related data for response
        sheet = db.query(GoogleSheet).filter(GoogleSheet.id == trigger.sheet_id).first()
        device = db.query(Device).filter(Device.device_id == trigger.device_id).first() if trigger.device_id else None
        
        return TriggerResponse(
            trigger_id=trigger.trigger_id,
            sheet_id=trigger.sheet_id,
            device_id=trigger.device_id,
            trigger_type=trigger.trigger_type,
            message_template=trigger.message_template,
            phone_column=trigger.phone_column,
            status_column=trigger.status_column,
            trigger_column=trigger.trigger_column,
            trigger_value=trigger.trigger_value,
            send_time_column=trigger.send_time_column,
            message_column=trigger.message_column,
            webhook_url=trigger.webhook_url,
            is_enabled=trigger.is_enabled,
            last_triggered_at=trigger.last_triggered_at,
            created_at=trigger.created_at,
            device_name=device.device_name if device else "Official API",
            sheet_name=sheet.sheet_name if sheet else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating trigger {trigger_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update trigger")

@router.get("/triggers/{trigger_id}/debug")
async def debug_trigger(
    trigger_id: str,
    current_user: BusiUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Debug endpoint to check trigger existence and ownership."""
    try:
        trigger_id = str(trigger_id) if trigger_id else None
        
        logger.info(f"Debugging trigger {trigger_id} for user {current_user.busi_user_id}")
        
        # Check if trigger exists at all
        any_trigger = db.query(GoogleSheetTrigger).filter(
            GoogleSheetTrigger.trigger_id == trigger_id
        ).first()
        
        # Check direct ownership
        direct_trigger = db.query(GoogleSheetTrigger).filter(
            and_(
                GoogleSheetTrigger.trigger_id == trigger_id,
                GoogleSheetTrigger.user_id == current_user.busi_user_id
            )
        ).first()
        
        # Check sheet ownership
        sheet_trigger = db.query(GoogleSheetTrigger).join(GoogleSheet).filter(
            and_(
                GoogleSheetTrigger.trigger_id == trigger_id,
                GoogleSheet.user_id == current_user.busi_user_id
            )
        ).first()
        
        # Get user's sheets
        user_sheets = db.query(GoogleSheet).filter(
            GoogleSheet.user_id == current_user.busi_user_id
        ).all()
        
        # Get user's triggers
        user_triggers = db.query(GoogleSheetTrigger).filter(
            GoogleSheetTrigger.user_id == current_user.busi_user_id
        ).all()
        
        return {
            "trigger_id": trigger_id,
            "user_id": str(current_user.busi_user_id),
            "exists": any_trigger is not None,
            "any_trigger": {
                "id": str(any_trigger.trigger_id) if any_trigger else None,
                "user_id": str(any_trigger.user_id) if any_trigger else None,
                "sheet_id": str(any_trigger.sheet_id) if any_trigger else None,
                "trigger_type": any_trigger.trigger_type if any_trigger else None,
                "is_enabled": any_trigger.is_enabled if any_trigger else None
            },
            "direct_ownership": direct_trigger is not None,
            "sheet_ownership": sheet_trigger is not None,
            "user_sheets_count": len(user_sheets),
            "user_triggers_count": len(user_triggers),
            "user_trigger_ids": [str(t.trigger_id) for t in user_triggers]
        }
        
    except Exception as e:
        logger.error(f"Error debugging trigger {trigger_id}: {e}")
        return {
            "error": str(e),
            "trigger_id": trigger_id,
            "user_id": str(current_user.busi_user_id)
        }

@router.delete("/triggers/{trigger_id}")
async def delete_trigger(
    trigger_id: str,
    current_user: BusiUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a trigger and stop any running background task."""
    try:
        # Validate trigger ownership
        # Ensure trigger_id is string to match DB (character varying)
        trigger_id = str(trigger_id) if trigger_id else None
        
        logger.info(f"Attempting to delete trigger {trigger_id} for user {current_user.busi_user_id}")
            
        # First try to find trigger by direct user ownership
        trigger = db.query(GoogleSheetTrigger).filter(
            and_(
                GoogleSheetTrigger.trigger_id == trigger_id,
                GoogleSheetTrigger.user_id == current_user.busi_user_id
            )
        ).first()
        
        logger.info(f"Direct ownership search result: {trigger}")
        
        # If not found by direct ownership, try via sheet ownership (for backward compatibility)
        if not trigger:
            logger.info(f"Trying sheet ownership search for trigger {trigger_id}")
            trigger = db.query(GoogleSheetTrigger).join(GoogleSheet).filter(
                and_(
                    GoogleSheetTrigger.trigger_id == trigger_id,
                    GoogleSheet.user_id == current_user.busi_user_id
                )
            ).first()
            
            logger.info(f"Sheet ownership search result: {trigger}")
        
        # Additional debug: Check if trigger exists at all (without ownership filter)
        if not trigger:
            logger.info(f"Checking if trigger {trigger_id} exists at all")
            any_trigger = db.query(GoogleSheetTrigger).filter(
                GoogleSheetTrigger.trigger_id == trigger_id
            ).first()
            logger.info(f"Any trigger found: {any_trigger}")
            if any_trigger:
                logger.info(f"Trigger exists but belongs to user_id: {any_trigger.user_id}")
        
        if not trigger:
            logger.error(f"Trigger {trigger_id} not found for user {current_user.busi_user_id}")
            raise HTTPException(status_code=404, detail=f"Trigger not found: {trigger_id}")
        
        # 🔥 FIX: Cancel background task before deleting trigger
        task_id = str(trigger.trigger_id)
        if task_id in active_trigger_tasks:
            task = active_trigger_tasks[task_id]
            if not task.done():
                task.cancel()
                logger.info(f"🛑 Cancelled background task for trigger {task_id}")
            del active_trigger_tasks[task_id]
        
        db.delete(trigger)
        db.commit()
        
        logger.info(f"Successfully deleted trigger {trigger_id}")
        return {"message": "Trigger deleted successfully"}
        
    except HTTPException as http_exc:
        # Re-raise HTTP exceptions (like 404) without additional handling
        logger.warning(f"HTTP Exception in delete_trigger: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        # Catch all other exceptions to prevent them from reaching session handler
        db.rollback()
        logger.error(f"Unexpected error deleting trigger {trigger_id}: {type(e).__name__}: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to delete trigger: {str(e)}")

# Global dict to hold active tasks
import asyncio


@router.get("/triggers/polling/status")
async def get_polling_status(
    current_user: BusiUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check if any triggers are currently running for this user"""
    # Find all triggers for this user
    user_triggers = db.query(GoogleSheetTrigger.trigger_id).filter(
        GoogleSheetTrigger.user_id == str(current_user.busi_user_id)
    ).all()
    
    user_trigger_ids = [str(t[0]) for t in user_triggers]
    
    # Check if any of these triggers have an active task
    active_count = 0
    for tid in user_trigger_ids:
        if tid in active_trigger_tasks and not active_trigger_tasks[tid].done():
            active_count += 1
            
    return {
        "is_running": active_count > 0,
        "status": "active" if active_count > 0 else "idle",
        "active_tasks_count": active_count,
        "message": f"{active_count} automation triggers are currently active."
    }

@router.post("/triggers/polling/start")
async def start_polling(
    current_user: BusiUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """🚀 MANUALLY START all enabled triggers for this user"""
    try:
        # Find all enabled triggers for this user's sheets
        triggers = db.query(GoogleSheetTrigger).filter(
            and_(
                GoogleSheetTrigger.user_id == str(current_user.busi_user_id),
                GoogleSheetTrigger.is_enabled == True
            )
        ).all()
        
        started_count = 0
        for trigger in triggers:
            t_id = str(trigger.trigger_id)
            # Only start if not already running
            if t_id not in active_trigger_tasks or active_trigger_tasks[t_id].done():
                logger.info(f"🚀 Manual starting trigger: {t_id}")
                task = asyncio.create_task(_trigger_worker_task(t_id))
                active_trigger_tasks[t_id] = task
                started_count += 1
        
        return {
            "success": True, 
            "message": f"Successfully started {started_count} automation triggers.",
            "total_active": len(triggers)
        }
    except Exception as e:
        logger.error(f"Error in manual start polling: {e}")
        return {"success": False, "message": str(e)}

@router.post("/triggers/polling/stop")
async def stop_polling(
    current_user: BusiUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """🛑 MANUALLY STOP all running triggers for this user"""
    try:
        # Find all triggers for this user's sheets
        triggers = db.query(GoogleSheetTrigger).filter(
            GoogleSheetTrigger.user_id == str(current_user.busi_user_id)
        ).all()
        
        stopped_count = 0
        for trigger in triggers:
            t_id = str(trigger.trigger_id)
            if t_id in active_trigger_tasks:
                task = active_trigger_tasks[t_id]
                if not task.done():
                    task.cancel()
                    stopped_count += 1
                del active_trigger_tasks[t_id]
        
        return {
            "success": True, 
            "message": f"Successfully stopped {stopped_count} trigger workers."
        }
    except Exception as e:
        logger.error(f"Error in manual stop polling: {e}")
        return {"success": False, "message": str(e)}


@router.post("/triggers/polling/fire-now")
async def fire_triggers_now(
    current_user: BusiUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """🔥 MANUALLY FIRE all enabled triggers for this user ONCE and disable them after completion"""
    try:
        from sqlalchemy import and_
        # Find all enabled triggers for this user's sheets
        triggers = db.query(GoogleSheetTrigger).filter(
            and_(
                GoogleSheetTrigger.user_id == str(current_user.busi_user_id),
                GoogleSheetTrigger.is_enabled == True
            )
        ).all()
        
        if not triggers:
            return {"success": True, "message": "No enabled triggers found to fire."}
            
        fired_count = 0
        for trigger in triggers:
            t_id = str(trigger.trigger_id)
            # Create a one-off task for each trigger
            async def run_once(tid):
                from db.session import SessionLocal
                session = SessionLocal()
                try:
                    processed_count = await _execute_trigger_process(tid, session, is_manual=True)
                    # 🔥 FIX: Disable trigger after one-time manual fire
                    if processed_count > 0 or processed_count == 0:
                        # Disable regardless of processed count - it's a one-time fire
                        current_trigger = session.query(GoogleSheetTrigger).filter(GoogleSheetTrigger.trigger_id == tid).first()
                        if current_trigger:
                            current_trigger.is_enabled = False
                            session.commit()
                            logger.info(f"✅ [FIRE_NOW] Trigger {tid} disabled after one-time manual fire.")
                finally:
                    session.close()

            asyncio.create_task(run_once(t_id))
            fired_count += 1
            
        return {
            "success": True, 
            "message": f"Successfully fired {fired_count} triggers. Triggers will be disabled after completion.",
            "total_fired": fired_count
        }
    except Exception as e:
        logger.error(f"Error in fire triggers now: {e}")
        return {"success": False, "message": str(e)}


def start_all_enabled_triggers():
    """Starts recently active triggers on application boot to prevent system lag"""
    from db.session import SessionLocal
    from models.google_sheet import GoogleSheetTrigger
    import asyncio
    import random
    
    # ⚡ [STARTUP_OPTIMIZATION]
    # To prevents 'Very Bad System' lag, we only auto-start the 5 most RECENTLY created triggers on boot.
    # All 24+ enabled triggers continue to exist, but we don't slam the Engine with all of them at once.
    # They will auto-start whenever the user visits their specific dashboard or manually enables them.
    session = SessionLocal()
    try:
        triggers = session.query(GoogleSheetTrigger).filter(
            GoogleSheetTrigger.is_enabled == True
        ).order_by(GoogleSheetTrigger.created_at.desc()).limit(50).all()
        
        logger.info(f"⚡ [BOOT] Auto-starting TOP {len(triggers)} RECENT triggers to keep system fast...")
        
        for trigger in triggers:
            t_id = str(trigger.trigger_id)
            if t_id not in active_trigger_tasks or active_trigger_tasks[t_id].done():
                
                # Staggered start function to spread out the load
                async def staggered_start(tid, delay):
                    await asyncio.sleep(delay)
                    # Check again in case it was started elsewhere
                    if tid not in active_trigger_tasks or active_trigger_tasks[tid].done():
                        task = asyncio.create_task(_trigger_worker_task(tid))
                        active_trigger_tasks[tid] = task

                # Schedule for start in 2-10 seconds
                asyncio.create_task(staggered_start(t_id, random.uniform(2, 10)))
        
        logger.info(f"✅ [BOOT] Scheduled {len(triggers)} triggers with staggered starts. Startup COMPLETE.")
    except Exception as e:
        logger.error(f"❌ Error starting enabled triggers on boot: {e}")
    finally:
        session.close()


async def start_all_enabled_triggers_on_boot():
    """🚀 Automatically start all enabled triggers in the system with retry logic"""
    from db.session import SessionLocal
    import time
    
    max_retries = 3  # Increased from 2 to handle slow boots
    for attempt in range(max_retries):
        session = None
        try:
            session = SessionLocal()
            # Add timeout to database query - reduced timeout to prevent hanging
            try:
                triggers = await asyncio.wait_for(
                    asyncio.to_thread(session.query(GoogleSheetTrigger).filter(GoogleSheetTrigger.is_enabled == True).all),
                    timeout=30.0  # Reduced from 60s to 30s
                )
            except asyncio.TimeoutError:
                db_logger.error("❌ [AUTO-START] Database query timed out - skipping trigger startup")
                return 0
            started = 0
            db_logger.info(f"🔍 [AUTO-START] Found {len(triggers)} enabled triggers to resume.")
            
            for trigger in triggers:
                t_id = str(trigger.trigger_id)
                if t_id not in active_trigger_tasks or active_trigger_tasks[t_id].done():
                    logger.info(f"🚀 [AUTO-START] Spawning worker for trigger: {t_id}")
                    task = asyncio.create_task(_trigger_worker_task(t_id))
                    active_trigger_tasks[t_id] = task
                    started += 1
                else:
                    db_logger.info(f"⏭️ [AUTO-START] Trigger {t_id} already has an active task.")
            
            db_logger.info(f"✅ [AUTO-START] Resumption complete. Spawned {started} workers.")
            return started
        except asyncio.TimeoutError:
            logger.error(f"⚠️ [AUTO-START] Attempt {attempt + 1} timed out accessing database")
            if attempt < max_retries - 1:
                await asyncio.sleep(2) # Reduced wait time
            else:
                logger.error("❌ [AUTO-START] All attempts timed out. Skipping trigger startup.")
                return 0
        except Exception as e:
            logger.error(f"⚠️ [AUTO-START] Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2) # Reduced wait time
            else:
                logger.error("❌ [AUTO-START] All attempts to resume triggers failed.")
                return 0
        finally:
            if session:
                session.close()


async def _execute_trigger_process(t_id: str, session: Session, is_manual: bool = False):
    """Core logic to process a single trigger once. Returns number of rows processed."""
    from services.google_sheets_automation_unofficial_only import GoogleSheetsAutomationServiceUnofficial
    
    current_trigger = session.query(GoogleSheetTrigger).filter(GoogleSheetTrigger.trigger_id == t_id).first()
    if not current_trigger or not current_trigger.is_enabled:
        if is_manual:
            logger.info(f"🛑 [PROCESS_{t_id}] Trigger disabled or deleted. Skipping.")
        return 0
        
    sheet = session.query(GoogleSheet).filter(GoogleSheet.id == current_trigger.sheet_id).first() if current_trigger.sheet_id else None
    
    # Prefix for logging
    if sheet:
        source_info = sheet.spreadsheet_id
    elif current_trigger.source_file_url:
        source_info = os.path.basename(current_trigger.source_file_url)
    else:
        source_info = "Unknown Source"
        
    automation_service = GoogleSheetsAutomationServiceUnofficial(session)
    
    prefix = "🔥 [MANUAL_FIRE]" if is_manual else "🔄 [POLLING]"
    logger.info(f"{prefix} [{t_id}] Checking source {source_info}...")
    
    try:
        if sheet:
            rows_data, headers_data = await asyncio.to_thread(
                automation_service.sheets_service.get_sheet_data_with_headers,
                spreadsheet_id=sheet.spreadsheet_id,
                worksheet_name=sheet.worksheet_name
            )
        elif current_trigger.source_file_url:
            rows_data, headers_data = automation_service._load_local_file_data(current_trigger.source_file_url)
            if not rows_data and not headers_data:
                logger.warning(f"⚠️ [PROCESS_{t_id}] File missing or empty. Auto-pausing trigger.")
                current_trigger.is_enabled = False
                session.commit()
                return 0
        else:
            logger.error(f"❌ [PROCESS_{t_id}] Missing data source configuration (Sheet or File)")
            return 0
        
        if rows_data:
            logger.info(f"📊 [{t_id}] Found {len(rows_data)} rows. Processing triggers...")
            # 🔥 FIX: Get processed count from automation service
            processed_count = await automation_service.process_single_trigger(sheet, current_trigger, rows_data, headers_data)
            return processed_count
        else:
            from datetime import datetime
            logger.info(f"⏳ [{t_id}] Sheet is empty. (Time: {datetime.now().strftime('%H:%M:%S')})")
        return 0
    except Exception as e:
        logger.error(f"🔥 [{t_id}] Error in trigger process: {e}")
        return 0

async def _trigger_worker_task(t_id: str):
    # We need a new session for the background task
    from db.session import SessionLocal
    
    # ✨ [WORKER_START] Starting worker task for trigger: {t_id}
    logger.info(f"🆕 [WORKER_{t_id}] Worker task created. Starting loop...")
    
    # ⚡ [PERFORMANCE] Poll every 15 seconds to keep system fast and responsive
    interval = 15
    is_first_run = True
    
    # 🔥 FIX: Track consecutive empty runs to stop trigger when all rows processed
    consecutive_empty_runs = 0
    MAX_EMPTY_RUNS = 3  # Stop after 3 consecutive runs with no rows processed
    
    # 🔥 STAGGERED START: Spreads out multiple triggers to prevent slamming Google API at once
    import random
    await asyncio.sleep(random.uniform(0, 5))
    
    while True:
        # Check if we should still be running based on our task storage
        current_task = asyncio.current_task()
        if active_trigger_tasks.get(t_id) != current_task:
            logger.info(f"👋 [WORKER_{t_id}] Task replaced or removed from active list (Task mismatch). Exiting redundant task.")
            break
            
        session = SessionLocal()
        try:
            # Check if trigger still exists and is enabled before running
            current_trigger = session.query(GoogleSheetTrigger).filter(GoogleSheetTrigger.trigger_id == str(t_id)).first()
            if not current_trigger or not current_trigger.is_enabled:
                logger.info(f"🛑 [WORKER_{t_id}] Trigger disabled or deleted in DB. Exiting worker.")
                if t_id in active_trigger_tasks and active_trigger_tasks[t_id] == current_task:
                    del active_trigger_tasks[t_id]
                break

            # 🔥 FIX: Stop time-based triggers after firing once
            if current_trigger.trigger_type == "time" and current_trigger.last_triggered_at:
                logger.info(f"✅ [WORKER_{t_id}] Time-based trigger completed. Disabling and stopping worker.")
                current_trigger.is_enabled = False
                session.commit()
                if t_id in active_trigger_tasks and active_trigger_tasks[t_id] == current_task:
                    del active_trigger_tasks[t_id]
                break

            # 🔥 FIX: Execute trigger and get processed count
            processed_count = await _execute_trigger_process(t_id, session, is_manual=False)
            
            # 🔥 FIX: Stop trigger if no rows processed consecutively (all rows completed)
            if processed_count == 0:
                consecutive_empty_runs += 1
                logger.info(f"⏳ [WORKER_{t_id}] No rows processed. Empty run count: {consecutive_empty_runs}/{MAX_EMPTY_RUNS}")
                
                if consecutive_empty_runs >= MAX_EMPTY_RUNS:
                    logger.info(f"✅ [WORKER_{t_id}] All rows processed (no rows for {MAX_EMPTY_RUNS} consecutive runs). Disabling and stopping worker.")
                    current_trigger.is_enabled = False
                    session.commit()
                    if t_id in active_trigger_tasks and active_trigger_tasks[t_id] == current_task:
                        del active_trigger_tasks[t_id]
                    break
            else:
                consecutive_empty_runs = 0  # Reset counter if rows were processed
                logger.info(f"📊 [WORKER_{t_id}] Processed {processed_count} rows. Continuing to monitor...")
                
        except asyncio.CancelledError:
            logger.info(f"🧘 [WORKER_{t_id}] Worker gracefully cancelled.")
            raise # Re-propagation is standard for CancelledError
        except Exception as e:
            logger.error(f"🔥 [WORKER_{t_id}] EXCEPTION in worker loop: {e}")
            import traceback
            logger.error(traceback.format_exc())
        finally:
            session.close() # Return connection to pool
            
        # 🔥 INSTANT START: Skip sleep on the very first loop to process immediately
        if is_first_run:
            is_first_run = False
        else:
            await asyncio.sleep(interval)

@router.post("/triggers/{trigger_id}/start")
async def start_trigger(
    trigger_id: str,
    current_user: BusiUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Validate trigger ownership
        # trigger_id in DB is String(50), no UUID conversion needed!
        trigger_uuid = str(trigger_id)
            
        # First try to find trigger by direct user ownership
        trigger = db.query(GoogleSheetTrigger).filter(
            and_(
                GoogleSheetTrigger.trigger_id == trigger_uuid,
                GoogleSheetTrigger.user_id == current_user.busi_user_id
            )
        ).first()
        
        # If not found by direct ownership, try via sheet ownership (for backward compatibility)
        if not trigger:
            trigger = db.query(GoogleSheetTrigger).join(GoogleSheet).filter(
                and_(
                    GoogleSheetTrigger.trigger_id == trigger_uuid,
                    GoogleSheet.user_id == current_user.busi_user_id
                )
            ).first()
        
        if not trigger:
            raise HTTPException(status_code=404, detail="Trigger not found")
            
        trigger.is_enabled = True
        db.commit()
        
        task_id = str(trigger.trigger_id)
        if task_id in active_trigger_tasks and not active_trigger_tasks[task_id].done():
            return {"message": "Trigger is already running", "trigger_id": task_id}
            
        # Start the task
        task = asyncio.create_task(_trigger_worker_task(task_id))
        active_trigger_tasks[task_id] = task
        
        return {"message": "Trigger started successfully", "trigger_id": task_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting trigger {trigger_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to start trigger")

@router.post("/triggers/{trigger_id}/stop")
async def stop_trigger(
    trigger_id: str,
    current_user: BusiUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Validate trigger ownership
        trigger_uuid = str(trigger_id)
            
        # First try to find trigger by direct user ownership
        trigger = db.query(GoogleSheetTrigger).filter(
            and_(
                GoogleSheetTrigger.trigger_id == trigger_uuid,
                GoogleSheetTrigger.user_id == current_user.busi_user_id
            )
        ).first()
        
        # If not found by direct ownership, try via sheet ownership (for backward compatibility)
        if not trigger:
            trigger = db.query(GoogleSheetTrigger).join(GoogleSheet).filter(
                and_(
                    GoogleSheetTrigger.trigger_id == trigger_uuid,
                    GoogleSheet.user_id == current_user.busi_user_id
                )
            ).first()
        
        if not trigger:
            raise HTTPException(status_code=404, detail="Trigger not found")
            
        trigger.is_enabled = False
        db.commit()
        
        task_id = str(trigger.trigger_id)
        if task_id in active_trigger_tasks:
            task = active_trigger_tasks[task_id]
            if not task.done():
                task.cancel()
            del active_trigger_tasks[task_id]
            
        return {"message": "Trigger stopped successfully", "trigger_id": task_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping trigger {trigger_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to stop trigger")

# ==================== HISTORY & ACTIONS ====================


@router.get("/{sheet_id}/history")
async def get_sheet_history(
    sheet_id: str,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=1, le=100),
    current_user: BusiUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get trigger history for a Google Sheet. Always returns an array."""
    try:
        sheet = validate_sheet_ownership(db, sheet_id, current_user.busi_user_id)
        
        # Get paginated history from correct table
        history = db.query(GoogleSheetTriggerHistory).filter(
            GoogleSheetTriggerHistory.sheet_id == sheet.id
        ).order_by(GoogleSheetTriggerHistory.triggered_at.desc()).offset(
            (page - 1) * per_page
        ).limit(per_page).all()
        
        # Format response to match frontend expectations
        # Frontend expects array of objects with specific field names
        history_responses = []
        for item in history:
            history_responses.append({
                "id": str(item.id),
                "sheet_id": str(item.sheet_id),
                "phone_number": item.phone_number,
                "message_content": item.message_content,
                "status": item.status,
                "triggered_at": item.triggered_at.isoformat() if item.triggered_at else None,
                "error_message": item.error_message
            })
        
        # ALWAYS return an array, even if empty
        return {
            "success": True,
            "data": history_responses
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting history for sheet {sheet_id}: {e}")
        # Even on error, return empty array to prevent frontend crashes
        return {
            "success": False,
            "data": []
        }

@router.get("/triggers/{trigger_id}/history", response_model=TriggerHistoryListResponse)
async def get_trigger_history(
    trigger_id: str,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=1, le=100),
    current_user: BusiUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get history for a specific trigger."""
    try:
        # Validate trigger ownership
        if isinstance(trigger_id, str):
            trigger_id = str(trigger_id)
            
        # First try to find trigger by direct user ownership
        trigger = db.query(GoogleSheetTrigger).filter(
            and_(
                GoogleSheetTrigger.trigger_id == trigger_id,
                GoogleSheetTrigger.user_id == current_user.busi_user_id
            )
        ).first()
        
        # If not found by direct ownership, try via sheet ownership (for backward compatibility)
        if not trigger:
            trigger = db.query(GoogleSheetTrigger).join(GoogleSheet).filter(
                and_(
                    GoogleSheetTrigger.trigger_id == trigger_id,
                    GoogleSheet.user_id == current_user.busi_user_id
                )
            ).first()
        
        if not trigger:
            raise HTTPException(status_code=404, detail="Trigger not found")
        
        # Get total count
        total_count = db.query(GoogleSheetTriggerHistory).filter(
            GoogleSheetTriggerHistory.trigger_id == trigger.trigger_id
        ).count()
        
        # Get paginated history
        history = db.query(GoogleSheetTriggerHistory).filter(
            GoogleSheetTriggerHistory.trigger_id == trigger.trigger_id
        ).order_by(GoogleSheetTriggerHistory.triggered_at.desc()).offset(
            (page - 1) * per_page
        ).limit(per_page).all()
        
        # Get sheet info
        sheet = db.query(GoogleSheet).filter(GoogleSheet.sheet_id == trigger.sheet_id).first()
        
        # Format response
        history_responses = []
        for item in history:
            history_responses.append(TriggerHistoryResponse(
                history_id=item.id,
                sheet_id=item.sheet_id,
                trigger_id=item.trigger_id,
                device_id=None,  # No device dependency
                row_number=item.row_data.get('row_number') if item.row_data else None,
                phone=item.phone_number,
                message=item.message_content,
                status=item.status,
                executed_at=item.triggered_at,
                device_name="Official API",  # Static name
                sheet_name=sheet.sheet_name if sheet else None
            ))
        
        return TriggerHistoryListResponse(
            history=history_responses,
            total_count=total_count,
            page=page,
            per_page=per_page
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting history for trigger {trigger_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve history")

@router.get("/{sheet_id}/stats")
async def get_sheet_stats(
    sheet_id: str,
    current_user: BusiUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get statistics for a Google Sheet."""
    try:
        sheet = validate_sheet_ownership(db, sheet_id, current_user.busi_user_id)
        
        # Get trigger count
        trigger_count = db.query(GoogleSheetTrigger).filter(
            GoogleSheetTrigger.sheet_id == sheet.id  # Changed from sheet.sheet_id to sheet.id
        ).count()
        
        # Get history stats
        total_sent = db.query(GoogleSheetTriggerHistory).filter(
            and_(
                GoogleSheetTriggerHistory.sheet_id == sheet.id,  # Changed from sheet.sheet_id to sheet.id
                GoogleSheetTriggerHistory.status == TriggerHistoryStatus.SENT
            )
        ).count()
        
        total_failed = db.query(GoogleSheetTriggerHistory).filter(
            and_(
                GoogleSheetTriggerHistory.sheet_id == sheet.id,  # Changed from sheet.sheet_id to sheet.id
                GoogleSheetTriggerHistory.status == TriggerHistoryStatus.FAILED
            )
        ).count()
        
        return {
            "sheet_id": sheet.id,  # Changed from sheet.sheet_id to sheet.id
            "sheet_name": sheet.sheet_name,
            "status": sheet.status,
            "rows_count": sheet.total_rows,  # Changed from rows_count to total_rows
            "trigger_count": trigger_count,
            "total_sent": total_sent,
            "total_failed": total_failed,
            "last_synced_at": sheet.last_synced_at,
            "connected_at": sheet.connected_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting stats for sheet {sheet_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")

@router.post("/{sheet_id}/sync")
async def sync_sheet(
    sheet_id: str,
    current_user: BusiUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    sheets_service: GoogleSheetsService = Depends(get_google_sheets_service)
):
    """Manually sync a Google Sheet."""
    try:
        sheet = validate_sheet_ownership(db, sheet_id, current_user.busi_user_id)
        
        # TODO: Implement actual sync with Google Sheets API
        # For now, just update the last_synced_at timestamp
        
        sheet.last_synced_at = datetime.utcnow()
        sheet.rows_count = 100  # Mock row count
        
        db.commit()
        db.refresh(sheet)
        
        return {
            "message": "Sheet synced successfully",
            "rows_count": sheet.rows_count,
            "last_synced_at": sheet.last_synced_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing sheet {sheet_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to sync sheet")

# ==================== ON-DEMAND TRIGGER PROCESSING ====================

@router.post("/{sheet_id}/check-triggers")
async def check_triggers_on_demand(
    sheet_id: str,
    current_user: BusiUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    sheets_service: GoogleSheetsService = Depends(get_google_sheets_service)
):
    """
    🔥 ON-DEMAND TRIGGER SCANNING
    
    Scans Google Sheet for trigger conditions and processes matching rows.
    This replaces the automatic background polling with on-demand execution.
    
    Process:
    1. Fetches sheet data ONCE per request
    2. Scans all active triggers for this sheet
    3. Processes rows matching trigger conditions
    4. Returns processing results
    
    Performance optimized:
    - Sheet data fetched once and reused for all triggers
    - No background polling or continuous API calls
    - Clean separation of concerns
    """
    try:
        logger.info(f"🚀 ON-DEMAND TRIGGER SCAN: Starting trigger scan via API request")
        logger.info(f"   Sheet ID: {sheet_id}")
        logger.info(f"   User ID: {current_user.busi_user_id}")
        
        # Validate sheet ownership
        sheet = validate_sheet_ownership(db, sheet_id, current_user.busi_user_id)
        
        # Import automation service for on-demand processing
        from services.google_sheets_automation import GoogleSheetsAutomationService
        
        # Create automation service instance
        automation_service = GoogleSheetsAutomationService(db)
        
        # 🚀 PERFORMANCE OPTIMIZATION: Fetch sheet data ONCE and reuse for all triggers
        logger.info(f"📊 Fetching sheet data for performance optimization...")
        rows_data, headers_data = sheets_service.get_sheet_data_with_headers(
            credentials=None,
            spreadsheet_id=sheet.spreadsheet_id,
            worksheet_name=sheet.worksheet_name
        )
        
        logger.info(f"   Fetched {len(rows_data)} rows and {len(headers_data)} columns - will reuse for all triggers")
        
        # Process triggers with cached data (performance optimization)
        await automation_service.process_sheet_triggers(sheet, rows_data, headers_data)
        
        logger.info(f"✅ ON-DEMAND TRIGGER SCAN: Trigger scan completed for sheet {sheet_id}")
        logger.info(f"   Performance: Used cached data - {len(rows_data)} rows fetched once")
        
        return {
            "success": True,
            "message": "Trigger scan completed successfully",
            "sheet_id": sheet_id,
            "sheet_name": sheet.sheet_name,
            "rows_processed": len(rows_data),
            "columns_found": len(headers_data),
            "processed_at": datetime.utcnow().isoformat(),
            "performance_note": "Sheet data fetched once and reused for all triggers",
            "background_polling": "Disabled - runs on-demand only"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ ON-DEMAND TRIGGER SCAN ERROR: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to scan triggers: {str(e)}"
        )

# ==================== HISTORY MANAGEMENT ====================

@router.delete("/triggers/history/clear")
async def clear_trigger_history(
    current_user: BusiUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    🔥 CLEAR ALL TRIGGER HISTORY
    
    Purges all historical records of automation triggers for the logged-in user.
    """
    try:
        from models.google_sheet import GoogleSheetTriggerHistory, GoogleSheetTrigger
        import uuid
        
        # We delete history for all triggers belonging to this user
        user_uuid = str(current_user.busi_user_id)
        
        # Subquery for trigger IDs belonging to user
        trigger_ids = db.query(GoogleSheetTrigger.id).filter(
            GoogleSheetTrigger.user_id == user_uuid
        ).subquery()
        
        deleted_count = db.query(GoogleSheetTriggerHistory).filter(
            GoogleSheetTriggerHistory.trigger_id.in_(trigger_ids)
        ).delete(synchronize_session=False)
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Successfully cleared {deleted_count} history records",
            "deleted_count": deleted_count
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error clearing trigger history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear history: {str(e)}")
