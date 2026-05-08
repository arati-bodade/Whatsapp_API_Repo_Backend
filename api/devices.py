from fastapi import APIRouter, Depends, HTTPException, Query, Request, Header
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging
from uuid import UUID

from db.session import get_db
from schemas.device import DeviceResponse as DeviceModelResponse, DeviceCreate, DeviceRegisterRequest, DeviceType, DeviceListResponse
from services.device_service import DeviceService
from models.device import SessionStatus
from services.device_sync_service import device_sync_service
from core.plan_validator import check_busi_user_plan
import time

from core.security import verify_token

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Devices"])

# 🔥 FIX: Per-user engine call throttle to prevent excessive WhatsApp Engine requests
LAST_ENGINE_CALL: dict = {}  # {user_id_or_device_id: timestamp}

def should_call_engine(key: str, cooldown: int = 15, bypass: bool = False) -> bool:
    """Prevent repeated engine calls per user/device within cooldown window (seconds)"""
    now = time.time()
    if not bypass and key in LAST_ENGINE_CALL:
        if now - LAST_ENGINE_CALL[key] < cooldown:
            return False
    LAST_ENGINE_CALL[key] = now
    return True

# 🔥 FIX: Simple response cache for device data (reduces repeated DB+engine queries)
DEVICE_RESPONSE_CACHE: dict = {}  # {cache_key: {"value": data, "time": timestamp}}

def get_cached_response(key: str, ttl: int = 10):
    """Get cached response if still valid within TTL seconds"""
    data = DEVICE_RESPONSE_CACHE.get(key)
    if data and time.time() - data["time"] < ttl:
        return data["value"]
    return None

def set_cached_response(key: str, value):
    """Cache a response with current timestamp"""
    DEVICE_RESPONSE_CACHE[key] = {"value": value, "time": time.time()}

def get_device_service(db: Session = Depends(get_db)) -> DeviceService:
    return DeviceService(db)

async def get_current_busi_user(authorization: str = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = authorization.split(" ")[1]
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return payload

@router.post("/register", response_model=DeviceModelResponse)
async def register_device(
    request: Request,
    token_payload: dict = Depends(get_current_busi_user),
    device_service: DeviceService = Depends(get_device_service)
):
    """Register a new device for the authenticated user"""
    try:
        user_id = str(token_payload.get("sub"))
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        # Parse request body manually to handle frontend format
        body = await request.json()
        device_name = body.get("device_name")
        device_type = body.get("device_type", "web")
        
        if not device_name:
            raise HTTPException(status_code=400, detail="device_name is required")
        
        # Create device register request
        device_request = DeviceRegisterRequest(
            user_id=str(user_id),
            device_name=device_name,
            device_type=DeviceType(device_type.lower())
        )
        
        # Register device using the service
        device = device_service.register_device(str(user_id), device_request)
        return device
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error registering device: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error registering device: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to register device: {str(e)}")

@router.get("/", response_model=List[DeviceModelResponse])
async def get_devices(
    session_status: Optional[str] = Query(None),
    token_payload: dict = Depends(get_current_busi_user),
    device_service: DeviceService = Depends(get_device_service)
):
    """Get all devices for the authenticated user, optionally filtered by status"""
    try:
        user_id = str(token_payload.get("sub"))
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        devices = device_service.get_user_devices(user_id, session_status)
        return devices
    except Exception as e:
        logger.error(f"Error getting devices: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get devices: {str(e)}")

@router.get("/unofficial/connected")
async def get_connected_unofficial_device(
    token_payload: dict = Depends(get_current_busi_user),
    device_service: DeviceService = Depends(get_device_service)
):
    """Get the first connected unofficial device for the authenticated user"""
    try:
        user_id = str(token_payload.get("sub"))
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        # 🔥 FIX: Throttle force sync to prevent spamming WhatsApp Engine
        # Only sync if cooldown has passed (20s per user)
        try:
            if should_call_engine(f"connected_sync_{user_id}", cooldown=20):
                from services.device_sync_service import device_sync_service
                from db.session import SessionLocal
                with SessionLocal() as sync_db:
                    device_sync_service.sync_user_devices(sync_db, user_id)
                logger.info(f"🔄 Synced devices for user {user_id} before returning connected list")
            else:
                logger.info(f"⏸️ Connected device sync throttled for user {user_id}")
        except Exception as sync_err:
            logger.warning(f"⚠️ Auto-sync failed for user {user_id}: {sync_err}")

        # Search for devices with 'connected' status only
        devices = device_service.get_user_devices(user_id, session_status="connected")
            
        # Filter for unofficial types only (web, mobile, desktop)
        unofficial_types = ["web", "mobile", "desktop"]
        connected_unofficial = [d for d in devices if d.device_type.value in unofficial_types]
        
        if connected_unofficial:
            # Return list format as expected by frontend's response.data.devices
            device_list = []
            for device in connected_unofficial:
                device_list.append({
                    "device_id": str(device.device_id),
                    "device_name": device.device_name,
                    "session_status": device.session_status.value,
                    "device_type": device.device_type.value
                })
            return {
                "success": True,
                "devices": device_list
            }
        else:
            return {
                "success": False,
                "devices": [],
                "message": "No connected unofficial device found"
            }
    except Exception as e:
        logger.error(f"Error getting connected unofficial device: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{device_id}")
async def get_device(
    device_id: str,
    device_service: DeviceService = Depends(get_device_service)
):
    """Get a specific device by ID"""
    try:
        device = device_service.get_device_by_id(device_id)
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        return device
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get device: {str(e)}")

@router.patch("/{device_id}/status")
async def update_device_status(
    device_id: str,
    request: dict,
    device_service: DeviceService = Depends(get_device_service)
):
    """Update device status - called by WhatsApp Engine"""
    try:
        logger.info(f"🔄 Updating device {device_id} status: {request}")
        
        # Extract session_status from request body - engine sends both 'status' and 'session_status'
        session_status = request.get("session_status") or request.get("status") or "unknown"
        ip_address = request.get("ip_address")
        
        # Update device status in database
        device = device_service.update_device_status(device_id, session_status, ip_address)
        
        if device:
            logger.info(f"✅ Device {device_id} status updated successfully")
            return {"success": True, "message": "Device status updated"}
        else:
            logger.warning(f"⚠️ Device {device_id} not found - returning 404")
            raise HTTPException(status_code=404, detail="Device not found")
            
    except Exception as e:
        # 🔥 CRITICAL: If the database is unreachable (OperationalError), 
        # we log the warning but return a 200 OK to the engine.
        # This prevents the engine from retrying indefinitely and flooding our logs/connections.
        error_msg = str(e)
        if "OperationalError" in error_msg or "SSL connection" in error_msg or "closed unexpectedly" in error_msg:
            logger.warning(f"⚠️ Database connection failure during status update for {device_id}. Suppressing retry flood.")
            return {"success": False, "message": "Database currently unavailable, update deferred"}
            
        logger.error(f"Error updating device {device_id} status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update device status: {str(e)}")

@router.post("/{device_id}/start")
async def start_device_session(
    device_id: str,
    device_service: DeviceService = Depends(get_device_service)
):
    """Start/initialize a WhatsApp session for a device - proxies to WhatsApp Engine"""
    try:
        # 🔥 FIX: Throttle start requests to prevent duplicate engine calls
        if not should_call_engine(f"start_{device_id}", cooldown=15):
            logger.info(f"⏸️ Start request throttled for device {device_id}")
            return {"status": "skipped_due_to_throttling", "message": "Start request throttled — please wait before retrying"}

        # Validate device exists in database first
        device = device_service.get_device_by_id(device_id)
        if not device:
            raise HTTPException(status_code=404, detail="Device not found in database")
        
        # Proxy to WhatsApp Engine
        from services.whatsapp_engine_service import WhatsAppEngineService
        engine_service = WhatsAppEngineService(device_service.db)
        result = engine_service.start_session(device_id)
        
        if result.get("success"):
            return {"status": "ok", "message": "Session start initiated", "data": result.get("result")}
        else:
            raise HTTPException(status_code=502, detail=result.get("error", "Failed to start session"))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting session for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start device session: {str(e)}")

@router.get("/{device_id}/qr")
async def get_device_qr(
    device_id: str,
    device_service: DeviceService = Depends(get_device_service)
):
    """Get QR code for a device - proxies to WhatsApp Engine with response caching"""
    try:
        # 🔥 FIX: Check response cache first to avoid repeated engine calls
        cache_key = f"qr_{device_id}"
        cached = get_cached_response(cache_key, ttl=10)
        if cached:
            logger.info(f"💾 Returning cached QR response for device {device_id}")
            return cached

        # Validate device exists in database first
        device = device_service.get_device_by_id(device_id)
        if not device:
            raise HTTPException(status_code=404, detail="Device not found in database")
        
        # Proxy to WhatsApp Engine
        from services.whatsapp_engine_service import WhatsAppEngineService
        engine_service = WhatsAppEngineService(device_service.db)
        result = engine_service.get_qr_code(device_id)
        
        if result.get("success"):
            data = result.get("data", {})
            qr_code = data.get("qr_code") or data.get("qr")
            if qr_code:
                response = {"qr_code": qr_code, "status": "qr_ready"}
                set_cached_response(cache_key, response)  # 🔥 Cache the response
                return response
            elif data.get("status") == "connected":
                response = {"qr_code": None, "status": "connected"}
                set_cached_response(cache_key, response)
                return response
            else:
                return {"qr_code": None, "status": data.get("status", "generating")}
        else:
            error = result.get("error", "QR code not available")
            if "ENGINE_NOT_READY" in str(error):
                raise HTTPException(status_code=502, detail=f"ENGINE_NOT_READY: {error}")
            raise HTTPException(status_code=404, detail=error)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting QR for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get QR code: {str(e)}")

@router.delete("/{device_id}")
async def delete_device(
    device_id: str,
    device_service: DeviceService = Depends(get_device_service)
):
    """Delete/logout a WhatsApp device"""
    try:
        result = device_service.logout_device(device_id)
        
        if result.get("success"):
            return {"message": "Device logged out successfully", "status": result.get("status")}
        else:
            error = result.get("error", "Failed to logout device")
            if error == "device_not_found":
                raise HTTPException(status_code=404, detail="Device not found")
            raise HTTPException(status_code=500, detail=error)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete device: {str(e)}")

@router.get("/official/list", response_model=Dict[str, Any])
async def get_official_devices(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    token_payload: dict = Depends(get_current_busi_user),
    device_service: DeviceService = Depends(get_device_service)
):
    """Get official WhatsApp devices for the authenticated user with pagination"""
    try:
        user_id = str(token_payload.get("sub"))
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        devices = device_service.get_devices_by_user_and_type(
            user_id, 
            DeviceType.OFFICIAL, 
            skip=(page - 1) * size, 
            limit=size
        )
        
        # Verify official config health to dynamically determine connection status
        from services.official_whatsapp_config_service import OfficialWhatsAppConfigService
        from models.device import SessionStatus
        config_service = OfficialWhatsAppConfigService(device_service.db)
        config = config_service.get_config_by_user_id(user_id)
        
        is_healthy = False
        if config and config.is_active and config.access_token:
            try:
                # This performs a real API call to Meta to verify token validity
                profile_result = config_service.get_business_profile(config)
                is_healthy = profile_result.success
            except Exception as ex:
                logger.warning(f"Failed to check official config health for user {user_id}: {ex}")
                is_healthy = False

        # Convert to response format
        device_list = []
        for device in devices:
            current_status = device.session_status
            
            # Dynamically push status change to database if it differs
            if is_healthy and current_status != SessionStatus.connected:
                device.session_status = SessionStatus.connected
                device_service.db.commit()
                current_status = SessionStatus.connected
            elif not is_healthy and current_status != SessionStatus.disconnected:
                device.session_status = SessionStatus.disconnected
                device_service.db.commit()
                current_status = SessionStatus.disconnected
                
            device_list.append({
                "device_id": str(device.device_id),
                "busi_user_id": str(device.busi_user_id),
                "device_name": device.device_name,
                "device_type": device.device_type.value,
                "session_status": current_status.value,
                "qr_last_generated": device.qr_last_generated.isoformat() if device.qr_last_generated else None,
                "ip_address": device.ip_address,
                "last_active": device.last_active.isoformat() if device.last_active else None,
                "created_at": device.created_at.isoformat() if device.created_at else None,
                "updated_at": device.updated_at.isoformat() if device.updated_at else None
            })
        
        return {
            "devices": device_list,
            "total": len(device_list),
            "page": page,
            "size": size
        }
    except Exception as e:
        logger.error(f"Error getting official devices: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get official devices: {str(e)}")

@router.get("/unofficial/list", response_model=Dict[str, Any])
async def get_unofficial_devices(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    sync: bool = Query(False), # 🔥 FIX: Changed from True to False — don't auto-sync on every request
    force: bool = Query(False), # 🔥 NEW: Force sync bypassing throttle
    token_payload: dict = Depends(get_current_busi_user),
    device_service: DeviceService = Depends(get_device_service)
):
    """Get unofficial WhatsApp devices for the authenticated user with pagination"""
    try:
        user_id = str(token_payload.get("sub"))
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        # 🔥 FIX: Only sync when explicitly requested AND throttle is not active
        if sync:
            if should_call_engine(f"unofficial_sync_{user_id}", cooldown=15, bypass=force):
                try:
                    logger.info(f"🔄 Syncing devices for user {user_id} (explicitly requested, force={force})...")
                    from db.session import SessionLocal
                    with SessionLocal() as sync_db:
                        device_sync_service.sync_user_devices(sync_db, user_id)
                except Exception as sync_err:
                    logger.warning(f"⚠️ Auto-sync failed for user {user_id}: {sync_err}")
            else:
                logger.info(f"⏸️ Sync throttled for user {user_id} — returning cached DB state")
        
        # Get all unofficial device types (web, mobile, desktop)
        unofficial_devices = []
        for device_type in [DeviceType.WEB, DeviceType.MOBILE, DeviceType.DESKTOP]:
            devices = device_service.get_devices_by_user_and_type(
                user_id, 
                device_type, 
                skip=(page - 1) * size, 
                limit=size
            )
            unofficial_devices.extend(devices)
        
        # Convert to response format
        device_list = []
        for device in unofficial_devices:
            device_list.append({
                "device_id": str(device.device_id),
                "busi_user_id": str(device.busi_user_id),
                "device_name": device.device_name,
                "device_type": device.device_type.value,
                "session_status": device.session_status.value,
                "qr_last_generated": device.qr_last_generated.isoformat() if device.qr_last_generated else None,
                "ip_address": device.ip_address,
                "last_active": device.last_active.isoformat() if device.last_active else None,
                "created_at": device.created_at.isoformat() if device.created_at else None,
                "updated_at": device.updated_at.isoformat() if device.updated_at else None
            })
        
        return {
            "devices": device_list,
            "total": len(device_list),
            "page": page,
            "size": size
        }
    except Exception as e:
        logger.error(f"Error getting unofficial devices: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get unofficial devices: {str(e)}")

@router.post("/heal/orphaned")
async def heal_orphaned_devices(
    device_service: DeviceService = Depends(get_device_service)
):
    """
    🔥 REQUIRED BY FRONTEND
    Scan all active devices and mark those not in engine as orphaned
    """
    try:
        logger.info("🛡️ HEAL ORPHANED API: Starting global scan")
        count = device_service.heal_orphaned_devices()
        return {
            "success": True,
            "message": f"Scan complete. {count} orphaned devices detected and updated.",
            "healed_count": count
        }
    except Exception as e:
        logger.error(f"❌ Heal failed: {e}")
        raise HTTPException(status_code=500, detail=f"Heal process failed: {str(e)}")

@router.post("/monitor/start")
async def start_device_monitoring():
    """
    🔥 NEW: Start continuous device monitoring service
    """
    try:
        from services.device_monitor_service import start_device_monitoring
        start_device_monitoring()
        logger.info("🚀 Device monitoring service started via API")
        return {
            "success": True,
            "message": "Device monitoring service started successfully"
        }
    except Exception as e:
        logger.error(f"❌ Failed to start monitoring: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start monitoring: {str(e)}")

@router.post("/monitor/stop")
async def stop_device_monitoring():
    """
    🔥 NEW: Stop continuous device monitoring service
    """
    try:
        from services.device_monitor_service import stop_device_monitoring
        stop_device_monitoring()
        logger.info("🛑 Device monitoring service stopped via API")
        return {
            "success": True,
            "message": "Device monitoring service stopped successfully"
        }
    except Exception as e:
        logger.error(f"❌ Failed to stop monitoring: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop monitoring: {str(e)}")

@router.post("/monitor/force-sync")
async def force_sync_all_devices():
    """
    🔥 NEW: Force immediate sync of all devices
    """
    try:
        from services.device_monitor_service import device_monitor_service
        result = device_monitor_service.force_sync_all_devices()
        return result
    except Exception as e:
        logger.error(f"❌ Force sync failed: {e}")
        raise HTTPException(status_code=500, detail=f"Force sync failed: {str(e)}")
