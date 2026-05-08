from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional

from db.session import get_db
from services.unified_service import UnifiedWhatsAppService
from services.uuid_service import UUIDService
from schemas.unified import (
    DeviceRegisterRequest, DeviceResponse,
    QRCodeResponse,
    UnifiedMessageRequest, UnifiedMessageResponse,
    MessageStatusUpdate,
    GroupInfo, GroupMember,
    WebhookMessage, WebhookStatusUpdate
)

router = APIRouter(prefix="/unified", tags=["Unified WhatsApp API"])


def get_unified_service(db: Session = Depends(get_db)) -> UnifiedWhatsAppService:
    return UnifiedWhatsAppService(db)


# Device Management Endpoints
@router.post("/devices/register", response_model=DeviceResponse)
async def register_device(
    device_data: DeviceRegisterRequest,
    reseller_id: str = Query(..., description="Reseller ID"),
    service: UnifiedWhatsAppService = Depends(get_unified_service)
):
    """Register new WhatsApp device"""
    try:
        result = service.register_device(device_data, reseller_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to register device: {str(e)}")


@router.delete("/devices/{device_id}")
async def delete_device(
    device_id: str,
    reseller_id: str = Query(..., description="Reseller ID"),
    service: UnifiedWhatsAppService = Depends(get_unified_service)
):
    """Delete WhatsApp device"""
    try:
        # ✅ Convert string UUID to UUID before passing to service
        device_uuid = UUIDService.safe_convert(device_id)
        service.delete_device(str(device_uuid), reseller_id)
        return {"message": "Device deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to delete device: {str(e)}")


@router.post("/devices/{device_id}/qr", response_model=QRCodeResponse)
async def generate_qr_code(
    device_id: str,
    reseller_id: str = Query(..., description="Reseller ID"),
    service: UnifiedWhatsAppService = Depends(get_unified_service)
):
    """Generate QR code for device"""
    try:
        # ✅ Convert string UUID to UUID before passing to service
        device_uuid = UUIDService.safe_convert(device_id)
        result = service.generate_qr_code(str(device_uuid), reseller_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to generate QR code: {str(e)}")


# Unified Message Endpoints
@router.post("/messages/send", response_model=UnifiedMessageResponse)
async def send_unified_message(
    message_data: UnifiedMessageRequest,
    service: UnifiedWhatsAppService = Depends(get_unified_service)
):
    """Send unified message supporting all types (text, file, base64, group)"""
    try:
        result = service.send_unified_message(message_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to send message: {str(e)}")


@router.get("/messages/{message_id}")
async def get_message_status(
    message_id: str,
    reseller_id: str = Query(..., description="Reseller ID"),
    service: UnifiedWhatsAppService = Depends(get_unified_service)
):
    """Get message status and details"""
    try:
        result = service.get_message_status(message_id, reseller_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Message not found: {str(e)}")


@router.patch("/messages/{message_id}/status")
async def update_message_status(
    message_id: str,
    status_update: MessageStatusUpdate,
    service: UnifiedWhatsAppService = Depends(get_unified_service)
):
    """Update message status"""
    try:
        result = service.update_message_status(message_id, status_update)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to update status: {str(e)}")


# Group Management Endpoints
@router.get("/messages/groups", response_model=List[GroupInfo])
async def get_groups(
    reseller_id: str = Query(..., description="Reseller ID"),
    service: UnifiedWhatsAppService = Depends(get_unified_service)
):
    """Get all WhatsApp groups for reseller"""
    try:
        result = service.get_groups(reseller_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to get groups: {str(e)}")


@router.get("/messages/groups/{group_id}/members", response_model=List[GroupMember])
async def get_group_members(
    group_id: str,
    reseller_id: str = Query(..., description="Reseller ID"),
    service: UnifiedWhatsAppService = Depends(get_unified_service)
):
    """Get all members of a specific group"""
    try:
        result = service.get_group_members(group_id, reseller_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to get group members: {str(e)}")


# Webhook Endpoints
@router.post("/messages/webhook")
async def webhook_message(
    webhook_data: WebhookMessage,
    service: UnifiedWhatsAppService = Depends(get_unified_service)
):
    """Process incoming webhook messages"""
    try:
        result = service.process_webhook_message(webhook_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process webhook: {str(e)}")


@router.post("/messages/webhook/status")
async def webhook_status_update(
    webhook_data: WebhookStatusUpdate,
    service: UnifiedWhatsAppService = Depends(get_unified_service)
):
    """Process webhook status updates"""
    try:
        result = service.process_webhook_status_update(webhook_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process status update: {str(e)}")
