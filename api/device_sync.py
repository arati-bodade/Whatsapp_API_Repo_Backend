"""
🔧 STEP 2: AUTO DEVICE SYNC LOGIC

Implement or fix a sync-devices endpoint
On sync:
    - Fetch devices from WhatsApp Engine
    - Insert missing devices into DB
    - Update user_id ownership correctly
    - Disable or remove stale devices that return 404 from engine
Ensure sync runs safely multiple times (idempotent)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from db.session import get_db
from models import BusiUser  # Fixed: Use BusiUser instead of Business
from api.google_sheets import get_current_user  # Fixed: Import from google_sheets
from services.device_sync_service import device_sync_service
from services.device_validator import validate_device_before_send
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/sync-devices", response_model=Dict[str, Any])
async def sync_user_devices(
    current_user: BusiUser = Depends(get_current_user),  # Fixed: BusiUser
    db: Session = Depends(get_db)
):
    """
    🔥 AUTO DEVICE SYNC ENDPOINT
    
    Sync devices from WhatsApp Engine to database for current user
    Auto-creates missing devices with proper ownership
    """
    try:
        logger.info(f"🔄 SYNC DEVICES API: User {current_user.busi_user_id}")
        
        result = device_sync_service.sync_user_devices(db, str(current_user.busi_user_id))
        
        if result["success"]:
            logger.info(f"✅ SYNC SUCCESS: {result}")
            return {
                "success": True,
                "message": "Devices synced successfully",
                "data": result
            }
        else:
            logger.error(f"❌ SYNC FAILED: {result}")
            raise HTTPException(status_code=500, detail=result.get("error", "Sync failed"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Sync devices error: {e}")
        raise HTTPException(status_code=500, detail="Failed to sync devices")

@router.post("/sync-device/{device_id}", response_model=Dict[str, Any])
async def ensure_device_exists(
    device_id: str,
    current_user: BusiUser = Depends(get_current_user),  # Fixed: BusiUser
    db: Session = Depends(get_db)
):
    """
    Ensure a specific device exists for the current user
    Auto-creates if missing
    """
    try:
        logger.info(f"🔍 ENSURE DEVICE API: {device_id} for user {current_user.busi_user_id}")
        
        result = device_sync_service.ensure_device_exists(db, str(current_user.busi_user_id), device_id)
        
        if result["success"]:
            logger.info(f"✅ ENSURE DEVICE SUCCESS: {result}")
            return {
                "success": True,
                "message": f"Device {device_id} ensured successfully",
                "action": result.get("action", "found"),
                "data": {
                    "device_id": device_id,
                    "device_name": result["device"].device_name if result.get("device") else None,
                    "session_status": result["device"].session_status if result.get("device") else None
                }
            }
        else:
            logger.error(f"❌ ENSURE DEVICE FAILED: {result}")
            raise HTTPException(status_code=404, detail=result.get("error", "Device not found"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Ensure device error: {e}")
        raise HTTPException(status_code=500, detail="Failed to ensure device")

@router.get("/validate-device/{device_id}", response_model=Dict[str, Any])
async def validate_device_for_user(
    device_id: str,
    current_user: BusiUser = Depends(get_current_user),  # Fixed: BusiUser
    db: Session = Depends(get_db)
):
    """
    Validate device ownership and status for current user
    Auto-creates missing devices
    """
    try:
        logger.info(f"🔍 VALIDATE DEVICE API: {device_id} for user {current_user.busi_user_id}")
        
        result = validate_device_before_send(db, device_id, str(current_user.busi_user_id))
        
        if result["valid"]:
            logger.info(f"✅ DEVICE VALID: {device_id}")
            return {
                "success": True,
                "valid": True,
                "device_id": device_id,
                "device_name": result["device"].device_name,
                "session_status": result["device"].session_status,
                "message": "Device is valid and ready"
            }
        else:
            logger.error(f"❌ DEVICE INVALID: {device_id} - {result.get('error')}")
            return {
                "success": False,
                "valid": False,
                "device_id": device_id,
                "error": result.get("error"),
                "message": "Device validation failed"
            }
            
    except Exception as e:
        logger.error(f"❌ Validate device error: {e}")
        return {
            "success": False,
            "valid": False,
            "device_id": device_id,
            "error": str(e),
            "message": "Device validation error"
        }

@router.post("/admin/sync-all-devices", response_model=Dict[str, Any])
async def sync_all_users_devices(
    current_user: BusiUser = Depends(get_current_user),  # Fixed: BusiUser
    db: Session = Depends(get_db)
):
    """
    Admin endpoint to sync devices for all users
    """
    try:
        # TODO: Add admin role check
        logger.info(f"🔄 ADMIN SYNC ALL DEVICES: User {current_user.busi_user_id}")
        
        result = device_sync_service.sync_all_users_devices(db)
        
        if result["success"]:
            logger.info(f"✅ ADMIN SYNC SUCCESS: {result}")
            return {
                "success": True,
                "message": "All users' devices synced successfully",
                "data": result
            }
        else:
            logger.error(f"❌ ADMIN SYNC FAILED: {result}")
            raise HTTPException(status_code=500, detail=result.get("error", "Admin sync failed"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Admin sync error: {e}")
        raise HTTPException(status_code=500, detail="Failed to sync all devices")
