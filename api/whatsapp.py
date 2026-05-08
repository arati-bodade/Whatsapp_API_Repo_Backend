from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from uuid import UUID
import base64
import io
from PIL import Image
from services.uuid_service import UUIDService

from db.session import get_db
from models.device import Device, SessionStatus
from datetime import datetime, timezone
from services.whatsapp_service import WhatsAppService
from schemas.whatsapp import (
    MessageRequest, MessageResponse,
    FileMessageRequest, FileMessageResponse,
    GroupMessageRequest, GroupMessageResponse,
    DeliveryReportResponse,
    DeviceRequest,
    DeviceResponse as APIResponseDevice, # Rename this one as it has 'success' field
    QRCodeResponse
)
from schemas.device import DeviceResponse as DeviceModelResponse # Use this one for DB mapping

router = APIRouter(tags=["WhatsApp"])


def get_whatsapp_service(db: Session = Depends(get_db)) -> WhatsAppService:
    return WhatsAppService(db)


# Message Endpoints
# Message Endpoints - MOVED TO api/user.py
# Use POST /api/user/message/unofficial instead for secure sending

# @router.post("/connect-simulate") <-- Keep this for now as it's used in Device UI logic
@router.post("/connect-simulate")
async def simulate_connection(
    device_id: str = Query(...),
    user_id: str = Query(...),
    whatsapp_service: WhatsAppService = Depends(get_whatsapp_service)
):
    """Simulate a successful QR scan and connection"""
    try:
        # ✅ Validate device_id format before processing
        UUIDService.safe_convert(device_id)
        result = whatsapp_service.simulate_connection(device_id, user_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to connect: {str(e)}")

@router.post("/send-message", response_model=MessageResponse)
async def send_message(
    message_request: MessageRequest,
    whatsapp_service: WhatsAppService = Depends(get_whatsapp_service)
):
    """Send message via WhatsApp Engine"""
    try:
        return whatsapp_service.send_message_via_engine(message_request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Reports and QR Code Endpoints
@router.get("/delivery-report", response_model=DeliveryReportResponse)
async def get_delivery_report(
    message_id: str = Query(...),
    user_id: str = Query(...),
    whatsapp_service: WhatsAppService = Depends(get_whatsapp_service)
):
    """Get delivery report for a message"""
    try:
        report = whatsapp_service.get_delivery_report(message_id, user_id)
        return report
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Delivery report not found: {str(e)}")


@router.post("/reset-qr")
async def reset_qr_code(
    device_id: str = Query(...),
    user_id: str = Query(...),
    whatsapp_service: WhatsAppService = Depends(get_whatsapp_service)
):
    """Reset QR code for device"""
    try:
        # ✅ Validate device_id format before processing
        UUIDService.safe_convert(device_id)
        result = whatsapp_service.reset_qr_code(device_id, user_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to reset QR code: {str(e)}")


@router.get("/get-qr", response_model=QRCodeResponse)
async def get_qr_code(
    device_id: str = Query(...),
    user_id: str = Query(...),
    whatsapp_service: WhatsAppService = Depends(get_whatsapp_service)
):
    """Get QR code for device (Legacy)"""
    try:
        # ✅ Validate device_id format before processing
        UUIDService.safe_convert(device_id)
        qr_data = whatsapp_service.get_qr_code(device_id, user_id)
        return qr_data
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"QR code not found: {str(e)}")



@router.get("/status")
async def get_whatsapp_status(
    device_id: Optional[str] = Query(None),
    whatsapp_service: WhatsAppService = Depends(get_whatsapp_service)
):
    """
    Bridge to Engine's status check or generic health check.
    This fixes 404 errors when frontend polls /api/whatsapp/status
    """
    try:
        if not device_id:
            return {"status": "active", "service": "whatsapp_api", "message": "Specify device_id to get real-time connection state"}
        
        # Sync specific device status with Engine
        status = whatsapp_service.sync_device_status(device_id)
        return {"status": status, "device_id": device_id}
    except Exception as e:
         raise HTTPException(status_code=400, detail=str(e))


@router.get("/{device_id}/qr")

async def get_device_qr(
    device_id: str,
    whatsapp_service: WhatsAppService = Depends(get_whatsapp_service)
):
    """Get QR code for device (New Standard)"""
    try:
        # Validate device_id format before processing
        UUIDService.safe_convert(device_id)
        
        # Import the engine service to fetch real QR
        from services.whatsapp_engine_service import WhatsAppEngineService
        engine_service = WhatsAppEngineService(whatsapp_service.db)
        
        # Fetch QR from WhatsApp Engine
        response = engine_service._make_request_with_retry("GET", f"/session/{device_id}/qr")
        
        if response and response.status_code == 200:
            data = response.json()
            if data.get('qr'):
                return {"qr_code": data['qr']}
            elif data.get('status') == 'connected':
                return {"qr_code": None, "status": "connected"}
            else:
                return {"qr_code": None, "status": data.get('status', 'generating')}
        elif response and response.status_code == 202:
            return {"qr_code": None, "status": "generating"}
        else:
            raise HTTPException(status_code=404, detail="QR code not available")
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate QR: {str(e)}")


# Device Management Endpoints
@router.post("/add-device", response_model=APIResponseDevice)
async def add_device(
    device_data: DeviceRequest,
    whatsapp_service: WhatsAppService = Depends(get_whatsapp_service)
):
    """Add new WhatsApp device"""
    try:
        result = whatsapp_service.add_device(device_data)
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Failed to add device: {str(e)}")


@router.post("/delete-device")
async def delete_device(
    device_id: str = Query(...),
    user_id: str = Query(...),
    whatsapp_service: WhatsAppService = Depends(get_whatsapp_service)
):
    """Delete WhatsApp device"""
    try:
        whatsapp_service.delete_device(device_id, user_id)
        return {"message": "Device deleted successfully"}
    except Exception as e:
        error_msg = str(e)
        if "Device not found" in error_msg:
             raise HTTPException(status_code=404, detail=error_msg)
        elif "Cannot delete device" in error_msg:
             raise HTTPException(status_code=409, detail=error_msg)
        raise HTTPException(status_code=400, detail=f"Failed to delete device: {error_msg}")


@router.get("/devices", response_model=List[DeviceModelResponse])
async def get_devices(
    user_id: str = Query(...),
    session_status: Optional[str] = Query(None),
    whatsapp_service: WhatsAppService = Depends(get_whatsapp_service)
):
    """Get all devices for a user, optionally filtered by status"""
    try:
        # Use raw SQL to avoid SQLAlchemy type casting issues
        user_id_str = str(user_id)
        
        query = """
            SELECT device_id, busi_user_id, device_name, device_type, session_status,
                   qr_last_generated, ip_address, last_active, created_at, updated_at
            FROM devices 
            WHERE busi_user_id = :user_id
        """
        params = {"user_id": user_id_str}
        
        if session_status:
            query += " AND session_status = :session_status"
            params["session_status"] = session_status
            
        query += " ORDER BY created_at DESC"

        result = whatsapp_service.db.execute(text(query), params).fetchall()
        
        # Manual serialization to handle Python Enum objects -> Pydantic str
        # Sync status for each device to ensure UI is up-to-date
        results = []
        for row in result:
            # Default to DB status
            current_status = row.session_status
            
            # Sync status if needed (if not already disconnected)
            # We assume 'disconnected' is a terminal state for the engine's perspective until reconnected
            if row.session_status != SessionStatus.disconnected.value:
                try:
                    # Sync with engine and get latest status
                    synced_status = whatsapp_service.sync_device_status(row.device_id)
                    # sync_device_status returns the new status string (value of enum)
                    if synced_status:
                        current_status = synced_status
                except Exception as sync_err:
                    print(f"Warning: Failed to sync status for device {row.device_id}: {sync_err}")
                    # Keep using the DB status if sync fails

            results.append({
                "device_id": row.device_id,
                "busi_user_id": row.busi_user_id,
                "device_name": row.device_name,
                "device_type": str(row.device_type).lower(),
                "session_status": current_status,
                "qr_last_generated": row.qr_last_generated,
                "ip_address": row.ip_address,
                "last_active": row.last_active,
                "created_at": row.created_at,
                "updated_at": row.updated_at
            })
        return results
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Failed to get devices: {str(e)}")
