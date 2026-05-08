from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Body, Query, Form, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import asyncio
import logging
import uuid
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from jose import jwt, JWTError

from db.session import get_db
from api.auth import get_current_user
from core.security import SECRET_KEY, ALGORITHM
from models.busi_user import BusiUser
from models.campaign import Campaign, MessageLog, CampaignStatus
from models.google_sheet import GoogleSheet
from schemas.campaign import CampaignCreateRequest, CampaignResponse
from services.campaign_service import CampaignService
from services.google_sheets_service import GoogleSheetsService
from core.plan_validator import check_busi_user_plan

logger = logging.getLogger(__name__)

router = APIRouter()

# Connection manager for websockets
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, campaign_id: str):
        await websocket.accept()
        if campaign_id not in self.active_connections:
            self.active_connections[campaign_id] = []
        self.active_connections[campaign_id].append(websocket)

    def disconnect(self, websocket: WebSocket, campaign_id: str):
        if campaign_id in self.active_connections:
            try:
                self.active_connections[campaign_id].remove(websocket)
            except ValueError:
                pass
            if not self.active_connections[campaign_id]:
                del self.active_connections[campaign_id]

    async def broadcast_campaign_progress(self, campaign_id: str, message: dict):
        if campaign_id in self.active_connections:
            for connection in self.active_connections[campaign_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    # Connection might be closed
                    pass

manager = ConnectionManager()

import os
import shutil
import json

@router.get("/", response_model=List[CampaignResponse])
async def list_campaigns(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: BusiUser = Depends(get_current_user)
):
    """List all campaigns for current user."""
    campaign_service = CampaignService(db)
    return campaign_service.get_user_campaigns(str(current_user.busi_user_id), skip=skip, limit=limit)

@router.post("/create", response_model=CampaignResponse)
async def create_new_campaign(
    payload: str = Form(...),
    file: Optional[UploadFile] = File(None),
    data_file: Optional[UploadFile] = File(None), # 🔥 NEW: Data source file (CSV/Excel)
    db: Session = Depends(get_db),
    current_user: BusiUser = Depends(get_current_user)
):
    try:
        # 1. Parse JSON payload
        try:
            request_dict = json.loads(payload)
            request = CampaignCreateRequest(**request_dict)
        except Exception as e:
            logger.error(f"Invalid JSON payload: {e}")
            raise HTTPException(status_code=400, detail=f"Invalid JSON payload: {str(e)}")

        # 2. Handle File Upload if exists
        media_url = None
        media_type = None
        if file:
            logger.info(f"[CREATE_CAMPAIGN] Handling file upload: {file.filename}")
            # Create uploads directory if it doesn't exist
            upload_dir = os.path.join("uploads", "campaign_media")
            os.makedirs(upload_dir, exist_ok=True)
            
            # Generate unique filename
            file_ext = os.path.splitext(file.filename)[1]
            unique_filename = f"{uuid.uuid4()}{file_ext}"
            file_path = os.path.join(upload_dir, unique_filename)
            
            # Save file
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Store absolute path as media_url
            media_url = os.path.abspath(file_path)
            
            # Determine media type (very basic)
            content_type = file.content_type or ""
            if "image" in content_type:
                media_type = "image"
            elif "video" in content_type:
                media_type = "video"
            elif "audio" in content_type:
                media_type = "audio"
            else:
                media_type = "document"
            
            logger.info(f"[CREATE_CAMPAIGN] File saved to: {media_url} (Type: {media_type})")

        # 3. Handle Data Source File Upload if exists
        source_file_url = None
        if data_file:
            logger.info(f"[CREATE_CAMPAIGN] Handling DATA SOURCE file: {data_file.filename}")
            upload_dir = os.path.join("uploads", "campaign_data")
            os.makedirs(upload_dir, exist_ok=True)
            
            file_ext = os.path.splitext(data_file.filename)[1].lower()
            unique_filename = f"data_{uuid.uuid4()}{file_ext}"
            file_path = os.path.join(upload_dir, unique_filename)
            
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(data_file.file, buffer)
            
            source_file_url = os.path.abspath(file_path)
            logger.info(f"[CREATE_CAMPAIGN] Data source saved to: {source_file_url}")

        # 4. Update request with media and data info
        if media_url:
            request.media_url = media_url
            request.media_type = media_type
        if source_file_url:
            request.source_file_url = source_file_url

        # NEW: Check Plan/Credits before creating campaign
        check_busi_user_plan(db, str(current_user.busi_user_id))

        campaign_service = CampaignService(db)
        logger.info(f"[CREATE_CAMPAIGN] Request data: {request.model_dump_json()}")
        return campaign_service.create_campaign(str(current_user.busi_user_id), request)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating campaign: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create campaign: {str(e)}")

@router.post("/{campaign_id}/start")
async def start_campaign(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user: BusiUser = Depends(get_current_user)
):
    # NEW: Check Plan/Credits before starting campaign
    check_busi_user_plan(db, str(current_user.busi_user_id))
    
    # 1. Verify Campaign Ownership
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id, 
        Campaign.busi_user_id == current_user.busi_user_id
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found or unauthorized")

    if not campaign.sheet_id and not campaign.source_file_url:
        raise HTTPException(status_code=400, detail="No source (Google Sheet or File) linked to this campaign")

    # 2. Fetch Sheet Data (Only if PENDING)
    formatted_rows = []
    if campaign.status == CampaignStatus.PENDING:
        if campaign.sheet_id:
            try:
                sheets_service = GoogleSheetsService()
                creds = sheets_service.get_service_account_credentials()
                
                sheet = db.query(GoogleSheet).filter(GoogleSheet.id == campaign.sheet_id).first()
                if not sheet:
                    raise HTTPException(status_code=404, detail="Google Sheet metadata not found")

                rows_data, headers = sheets_service.get_sheet_data_with_headers(
                    spreadsheet_id=sheet.spreadsheet_id, 
                    worksheet_name=sheet.worksheet_name or "Sheet1",
                    credentials=creds
                )
                
                # 🔥 SMART PHONE DETECTION: Look for common column names
                phone_col = "phone"
                if sheet.trigger_config and isinstance(sheet.trigger_config, dict):
                    phone_col = sheet.trigger_config.get("phone_column", phone_col)
                
                # Check headers to find the best candidate if the default fails
                if rows_data and headers:
                    headers_lower = [str(h).lower().strip() for h in headers]
                    phone_keywords = ['phone', 'mobile', 'number', 'contact', 'recipient', 'to', 'whatsapp', 'मोबाईल', 'फोन']
                    
                    found_col = None
                    # Try to find best match from keywords
                    for kw in phone_keywords:
                        if kw in headers_lower:
                            idx = headers_lower.index(kw)
                            found_col = headers[idx]
                            break
                    
                    if found_col:
                        phone_col = found_col
                    elif headers:
                        # Fallback to FIRST column if no phone column found (likely what the user intended)
                        phone_col = headers[0]
                        logger.warning(f"⚠️ Could not identify phone column. Defaulting to first column: {phone_col}")

                for row in rows_data:
                    data = row.get("data", {})
                    # Try specific phone_col, then general fallbacks
                    actual_phone = data.get(phone_col) or data.get("Phone") or data.get("Phone Number") or data.get("Mobile")
                    
                    if not actual_phone:
                        continue
                        
                    valid_phone = sheets_service.validate_phone_number(actual_phone)
                    
                    formatted_rows.append({
                        "phone": valid_phone or actual_phone,
                        "row_data": data
                    })
            except HTTPException:
                raise
            except Exception as e:
                msg = str(e)
                if "Service Account" in msg or "placeholder" in msg.lower():
                    msg = "Google Sheets credentials are not set up. Please update credentials/google-service-account.json."
                logger.error(f"Failed to process sheet for campaign {campaign_id}: {msg}")
                raise HTTPException(status_code=400, detail=msg)
                
        elif campaign.source_file_url:
            # 🔥 NEW: Process File-Based Campaign (CSV/Excel)
            try:
                from utils.file_parser import get_recipient_data_from_file
                logger.info(f"📁 Processing data file source: {campaign.source_file_url}")
                formatted_rows = get_recipient_data_from_file(campaign.source_file_url)
            except Exception as fe:
                logger.error(f"Failed to process file {campaign.source_file_url}: {fe}")
                raise HTTPException(status_code=400, detail=str(fe))

    # 3. Trigger Service Start
    try:
        # Create a new local session for the service to ensure it doesn't conflict with request cleanup
        campaign_service = CampaignService(db)
        result = await campaign_service.start_campaign(
            user_id=str(current_user.busi_user_id), 
            campaign_id=campaign_id, 
            rows_data=formatted_rows
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting campaign service for {campaign_id}: {e}")
        # Ensure we return a clean 500 error if service fails before response starts
        raise HTTPException(status_code=500, detail="Failed to initiate campaign worker.")

@router.post("/{campaign_id}/pause")
async def pause_campaign(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user: BusiUser = Depends(get_current_user)
):
    campaign_service = CampaignService(db)
    
    try:
        return await campaign_service.pause_campaign(str(current_user.busi_user_id), campaign_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pausing campaign {campaign_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to pause campaign.")

@router.post("/{campaign_id}/resume")
async def resume_campaign(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user: BusiUser = Depends(get_current_user)
):
    campaign_service = CampaignService(db)
    
    try:
        return await campaign_service.resume_campaign(str(current_user.busi_user_id), campaign_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resuming campaign {campaign_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to resume campaign.")

@router.get("/{campaign_id}/status")
async def get_campaign_status(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user: BusiUser = Depends(get_current_user)
):
    campaign_service = CampaignService(db)
    
    try:
        # Service handles DB and Redis status consolidation
        return await campaign_service.get_campaign_status(str(current_user.busi_user_id), campaign_id)
    except HTTPException:
        raise
    except (OperationalError, SQLAlchemyError) as e:
        logger.error(f"Database error during status check for {campaign_id}: {e}")
        raise HTTPException(status_code=503, detail="Database currently unavailable.")
    except Exception as e:
        logger.error(f"Unexpected error during status check for {campaign_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error fetching status.")

@router.get("/{campaign_id}/logs")
async def get_campaign_logs(
    campaign_id: str,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: BusiUser = Depends(get_current_user)
):
    try:
        campaign = db.query(Campaign).filter(
            Campaign.id == campaign_id, 
            Campaign.busi_user_id == current_user.busi_user_id
        ).first()
        
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
               
        logs = db.query(MessageLog).filter(
            MessageLog.campaign_id == campaign_id
        ).order_by(MessageLog.created_at.desc()).limit(limit).all()
        
        return {
            "logs": [
                {
                    "id": str(l.id),
                    "recipient": l.recipient,
                    "status": l.status,
                    "retry_count": l.retry_count,
                    "created_at": l.created_at.isoformat() if l.created_at else None,
                    "device_id": str(l.device_id) if l.device_id else None
                } for l in logs
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching logs for campaign {campaign_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch campaign logs.")

@router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user: BusiUser = Depends(get_current_user)
):
    """Delete a specific campaign."""
    campaign_service = CampaignService(db)
    success = campaign_service.delete_campaign(str(current_user.busi_user_id), campaign_id)
    if not success:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return {"status": "success", "message": "Campaign deleted"}

@router.websocket("/ws/{campaign_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    campaign_id: str, 
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for real-time campaign progress tracking."""
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)
        return

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise JWTError("Missing sub in token")
    except JWTError:
        await websocket.close(code=1008)
        return

    # Verify campaign exists (simple check)
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        await websocket.close(code=4004) # Not Found
        return

    await manager.connect(websocket, campaign_id)
    campaign_service = CampaignService(db)
    
    try:
        while True:
            # Poll status every 2 seconds
            try:
                status = await campaign_service.get_campaign_status(str(user_id), campaign_id)
                await websocket.send_json(status)
                
                if status.get("status") in ["Completed", "Failed"]:
                    # Wait a bit before closing to ensure UI gets the final state
                    await asyncio.sleep(2)
                    break
            except Exception as e:
                logger.error(f"WS status poll error for {campaign_id}: {e}")
                # Don't break on single error, but wait
                
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket, campaign_id)
