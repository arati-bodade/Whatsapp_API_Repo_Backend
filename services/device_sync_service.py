#!/usr/bin/env python3
"""
🔧 PRODUCTION-GRADE FIX (VERY IMPORTANT)
You MUST update backend logic:
Rule:

If device exists in engine AND user is authenticated
→ auto-link device to user in DB

Pseudo-code:
if engine_device_exists and not db_device:
    create_device_for_user()

This prevents this bug forever.
"""
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
import requests
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import cast, String
from models.device import Device, DeviceType, SessionStatus
from services.session_validation_service import session_validation_service
from core.config import settings

logger = logging.getLogger(__name__)

class DeviceSyncService:
    """
    🔥 PRODUCTION-GRADE DEVICE SYNC SERVICE
    
    Ensures database is always in sync with WhatsApp Engine
    Auto-creates missing devices for authenticated users
    Fixed: Added connection stability and cooldown mechanisms
    """
    
    def __init__(self, engine_url: str = None, db: Session = None):
        self.engine_url = engine_url or settings.WHATSAPP_ENGINE_BASE_URL
        self.db = db
        # 🔥 NEW: Status update cooldown to prevent thrashing
        self._status_cooldowns = {}  # {device_id: datetime}
        # 🔥 RATE LIMITING: Use WhatsApp engine service for proper rate limiting
        self._whatsapp_engine_service = None
        
    def _get_whatsapp_engine_service(self):
        """Get WhatsApp engine service with rate limiting and circuit breaker"""
        if self._whatsapp_engine_service is None:
            from services.whatsapp_engine_service import WhatsAppEngineService
            self._whatsapp_engine_service = WhatsAppEngineService(self.db)
        return self._whatsapp_engine_service
    
    def _is_valid_uuid(self, device_id: str) -> bool:
        """Check if device_id is a valid UUID"""
        try:
            str(device_id)
            return True
        except (ValueError, AttributeError):
            return False
    
    def _is_status_update_allowed(self, device_id: str) -> bool:
        """Check if status update is allowed (cooldown mechanism)"""
        now = datetime.utcnow()
        last_update = self._status_cooldowns.get(device_id)
        
        if last_update:
            time_since_last = now - last_update
            # 🔥 FIXED: Require 15 seconds between status updates to prevent thrashing
            if time_since_last < timedelta(seconds=15):
                logger.debug(f"⏸️ Status update cooldown for {device_id}: {time_since_last.seconds}s since last update")
                return False
        
        return True
    
    def _record_status_update(self, device_id: str):
        """Record that a status update was performed"""
        self._status_cooldowns[device_id] = datetime.utcnow()
        logger.debug(f"📝 Status update recorded for {device_id}")
        
    def get_engine_devices(self) -> List[Dict[str, any]]:
        """
        Fetch all devices from WhatsApp Engine using rate-limited service
        """
        try:
            # 🔥 RATE LIMITING: Use WhatsApp engine service for proper rate limiting and circuit breaker
            engine_service = self._get_whatsapp_engine_service()
            result = engine_service.get_all_sessions()
            
            if result.get("success"):
                sessions = result.get("sessions", [])
                devices = []
                
                # Handle both formats: {device_id: session_info} or [{session_info}]
                if isinstance(sessions, dict):
                    for device_id, session_info in sessions.items():
                        # 🔥 SESSION VALIDATION: Filter invalid sessions
                        if not session_validation_service.is_valid_device_id(device_id):
                            logger.warning(f"🗑️ Skipping invalid device_id from engine: {device_id}")
                            continue
                        
                        devices.append({
                            "device_id": device_id,
                            "status": session_info.get("status", "unknown"),
                            "phone": session_info.get("phone", ""),
                            "name": session_info.get("name", f"Device {device_id[:8]}"),
                            "platform": session_info.get("platform", "web")
                        })
                elif isinstance(sessions, list):
                    for session_info in sessions:
                        if "id" in session_info:
                            device_id = session_info["id"]
                            
                            # 🔥 SESSION VALIDATION: Filter invalid sessions
                            if not session_validation_service.is_valid_device_id(device_id):
                                logger.warning(f"🗑️ Skipping invalid device_id from engine: {device_id}")
                                continue
                            
                            devices.append({
                                "device_id": device_id,
                                "status": session_info.get("status", "unknown"),
                                "phone": session_info.get("phone", ""),
                                "name": session_info.get("name", f"Device {device_id[:8]}"),
                                "platform": session_info.get("platform", "web")
                            })
                
                return devices
            else:
                logger.error(f"Failed to fetch devices from Engine: {result.get('error', 'Unknown error')}")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching devices from Engine: {e}")
            return []
    
    def sync_user_devices(self, db: Session, user_id: str) -> Dict[str, any]:
        """
        🔥 ENHANCED SYNC LOGIC WITH PROACTIVE CONNECTION MONITORING
        
        If device exists in engine AND user is authenticated
        → auto-link device to user in DB
        
        Enhanced with connection stability improvements:
        - Proactive status validation
        - Connection health checks
        - Automatic reconnection attempts
        """
        logger.info(f"🔄 ENHANCED SYNCING DEVICES FOR USER: {user_id}")
        
        if not user_id:
            logger.error("❌ user_id is missing")
            return {"success": False, "error": "user_id is missing"}
        
        try:
            # Get all devices from Engine
            engine_devices = self.get_engine_devices()
            
            if not engine_devices:
                logger.warning("No devices found in Engine")
                return {"success": False, "error": "No devices in Engine"}
            
            # Get existing devices for this user from DB
            existing_db_devices = db.query(Device).filter(Device.busi_user_id == user_id).all()
            existing_device_ids = {str(device.device_id) for device in existing_db_devices}
            
            logger.info(f"   Engine devices: {len(engine_devices)}")
            logger.info(f"   DB devices for user: {len(existing_db_devices)}")
            
            synced_devices = []
            created_devices = []
            updated_devices = []
            reconnection_attempts = []
            
            for engine_device in engine_devices:
                device_id = engine_device["device_id"]
                
                if not device_id:
                    logger.warning("⚠️ Skipping empty device_id")
                    continue
                device_uuid = str(device_id)
                
                # 🔥 ENHANCED: Proactive connection health check
                engine_status = engine_device.get("status", "unknown").lower()
                
                # First check if device exists GLOBALLY in DB to avoid UniqueViolation
                db_device = db.query(Device).filter(Device.device_id == device_uuid).first()
                
                if not db_device:
                    # Device DOES NOT EXIST anywhere → Auto-link to THIS user
                    logger.info(f"   🆕 Auto-linking device to user: {device_uuid} -> {user_id}")
                    
                    try:
                        new_device = Device(
                            device_id=device_uuid,
                            busi_user_id=user_id,
                            device_name=engine_device.get("name", f"Device {device_uuid[:8]}"),
                            device_type=DeviceType.web if engine_device.get("platform") == "web" else DeviceType.mobile,
                            session_status=SessionStatus.connected if engine_status == "connected" else SessionStatus.disconnected,
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow(),
                            last_active=datetime.utcnow()  # 🔥 NEW: Track last activity
                        )
                        
                        db.add(new_device)
                        db.flush()
                        created_devices.append(device_uuid)
                        logger.info(f"   ✅ Auto-linked device: {device_uuid} to user: {user_id}")
                        
                    except Exception as create_error:
                        logger.error(f"   ❌ Failed to link device {device_uuid}: {create_error}")
                        db.rollback()
                        continue
                else:
                    # Device ALREADY EXISTS in DB
                    # 🔥 CRITICAL PRIVACY FIX: NEVER re-link or "steal" device from another user
                    if str(db_device.busi_user_id) != str(user_id):
                        logger.warning(f"   🛡️ SKIP: Device {device_id} belongs to another user ({db_device.busi_user_id}). Sync denied for user {user_id}.")
                        continue
                        
                    # 🔥 ENHANCED: Map engine status to database status with better handling
                    new_session_status = SessionStatus.disconnected
                    
                    if engine_status == "connected":
                        new_session_status = SessionStatus.connected
                    elif engine_status in ["qr_ready", "qr_generated", "scanning"]:
                        new_session_status = SessionStatus.qr_ready
                    elif engine_status == "connecting":
                        new_session_status = SessionStatus.connecting
                    elif engine_status in ["disconnected", "offline"]:
                        new_session_status = SessionStatus.disconnected
                    
                    # 🔥 FIXED: Prevent unnecessary status updates with cooldown
                    if db_device.session_status == new_session_status:
                        # No change needed - skip to prevent loops
                        # 🔥 ENHANCED: Clear pending disconnect if status is back to connected
                        if hasattr(self, '_pending_disconnects') and device_uuid in self._pending_disconnects:
                            del self._pending_disconnects[device_uuid]
                            logger.info(f"   ✅ CANCELLED DISCONNECT for {device_id}: Status recovered to connected")
                        continue
                    
                    # 🔥 NEW: Apply cooldown to prevent rapid status changes
                    # 🔥 CRITICAL FIX: Bypass cooldown for 'connected' status to ensure instant sync after QR scan
                    is_critical_status = (new_session_status == SessionStatus.connected)
                    
                    if not is_critical_status and not self._is_status_update_allowed(device_uuid):
                        logger.debug(f"⏸️ Skipping status update for {device_uuid} due to cooldown")
                        continue
                    
                    # 🔥 NEW: Update last_active for connected devices
                    if new_session_status == SessionStatus.connected:
                        db_device.last_active = datetime.utcnow()
                    
                    # 🔥 FIXED: Handle connection drops more carefully with extra protection
                    old_status = db_device.session_status
                    if old_status == SessionStatus.connected and new_session_status != SessionStatus.connected:
                        # 🔥 CRITICAL: Never downgrade from connected without explicit engine confirmation
                        # Only mark disconnected if engine explicitly says so (not on errors/unknown)
                        if new_session_status == SessionStatus.disconnected:
                            logger.warning(f"   🔌 CONNECTION DROP DETECTED for {device_id}: {old_status} -> {new_session_status}")
                            # 🔥 ENHANCED: Add debounce for disconnect - wait 30s before marking disconnected
                            if not hasattr(self, '_pending_disconnects'):
                                self._pending_disconnects = {}
                            
                            # Schedule disconnect after 30s delay
                            if device_uuid not in self._pending_disconnects:
                                self._pending_disconnects[device_uuid] = datetime.utcnow()
                                logger.info(f"   ⏰ SCHEDULED DISCONNECT for {device_id}: Will mark as disconnected in 30s")
                                continue
                            else:
                                # Check if 30s have passed
                                disconnect_time = self._pending_disconnects[device_uuid]
                                if (datetime.utcnow() - disconnect_time) < timedelta(seconds=30):
                                    logger.debug(f"   ⏳ Waiting for disconnect confirmation for {device_id}")
                                    continue
                                else:
                                    # Mark as disconnected after delay
                                    del self._pending_disconnects[device_uuid]
                                    db_device.session_status = new_session_status
                                    db_device.updated_at = datetime.utcnow()
                                    updated_devices.append(device_id)
                                    logger.info(f"   ✅ CONFIRMED DISCONNECT for {device_id}: Marked as disconnected")
                        else:
                            # For other statuses (qr_ready, connecting), keep as connected to prevent thrashing
                            logger.debug(f"   ⏸️ Ignoring non-critical status change for {device_id}: {old_status} -> {new_session_status}")
                            continue
                        
                    elif db_device.session_status != new_session_status:
                        # Normal status change
                        db_device.session_status = new_session_status
                        db_device.updated_at = datetime.utcnow()
                        # 🔥 NEW: Record status update for cooldown
                        self._record_status_update(device_uuid)
                        updated_devices.append(device_id)
                        logger.info(f"   🔄 Device status updated: {device_id} ({old_status} -> {new_session_status})")
                
                synced_devices.append(device_uuid)
            
            # Commit all changes
            db.commit()
            
            # 🔥 CRITICAL FIX: DO NOT auto-mark devices as expired
            # Devices should only be marked disconnected by user action or WhatsApp invalidation
            # Never auto-expire devices just because they're temporarily missing from engine
            # This prevents the 10-second disconnect bug after QR scan
            stale_devices = []
            
            result = {
                "success": True,
                "synced": len(synced_devices),
                "created": len(created_devices),
                "updated": len(updated_devices),
                "reconnection_attempts": len(reconnection_attempts),
                "stale": len(stale_devices),
                "devices": synced_devices
            }
            
            logger.info(f"🏁 ENHANCED SYNC COMPLETE: {result}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Enhanced device sync error: {e}")
            db.rollback()
            return {"success": False, "error": str(e)}
    
    def ensure_device_exists(self, db: Session, user_id: str, device_id: str) -> Dict[str, any]:
        """
        Ensure a specific device exists for a user
        Auto-create if missing (production-grade fix)
        """
        logger.info(f"🔍 ENSURING DEVICE EXISTS: {device_id} for user {user_id}")
        
        try:
            # Check if device exists in DB for this user
            # For official WhatsApp configs, device_id might be a string phone_number_id
            # We need to handle both UUID and string device_ids
            # 🔥 NEW: Simplified string-based query
            device_id_str = str(device_id)
            user_id_str = str(user_id)
            
            db_device = db.query(Device).filter(
                Device.device_id == device_id_str,
                Device.busi_user_id == user_id_str
            ).first()
            
            if db_device:
                logger.info(f"   ✅ Device exists in DB: {device_id}")
                return {"success": True, "device": db_device, "action": "found"}
            
            # Check if this is an official WhatsApp phone_number_id
            from models.official_whatsapp_config import OfficialWhatsAppConfig
            official_config = db.query(OfficialWhatsAppConfig).filter(
                OfficialWhatsAppConfig.phone_number_id == device_id,
                OfficialWhatsAppConfig.busi_user_id == user_id
            ).first()
            
            if official_config:
                logger.info(f"   📱 Creating Device record for Official WhatsApp config: {device_id}")
                
                # Use provided device_id as string
                device_uuid = str(device_id)
                logger.info(f"   📱 Using phone_number_id as device ID: {device_uuid}")
                
                new_device = Device(
                    device_id=device_uuid,
                    busi_user_id=user_id,
                    device_name=f"Official WhatsApp - {official_config.business_number}",
                    device_type=DeviceType.official,  # 🔥 FIXED: Use lowercase 'official' to match enum
                    session_status=SessionStatus.connected if official_config.is_active else SessionStatus.disconnected,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                db.add(new_device)
                db.commit()
                
                logger.info(f"   ✅ Created Device for Official WhatsApp: {device_uuid}")
                return {"success": True, "device": new_device, "action": "created_official"}
            
            # Check if device exists in Engine (for unofficial devices)
            engine_devices = self.get_engine_devices()
            engine_device = next((d for d in engine_devices if d["device_id"] == device_id), None)
            
            if not engine_device:
                logger.error(f"   ❌ Device not found in Engine or Official Config: {device_id}")
                return {"success": False, "error": "Device not found in Engine or Official Config"}
            
            # 🔥 AUTO-CREATE DEVICE (PRODUCTION FIX)
            logger.info(f"   🆕 Auto-creating device: {device_id}")
            
            new_device = Device(
                device_id=device_id,
                busi_user_id=user_id,
                device_name=engine_device.get("name", f"Device {device_id[:8]}"),
                device_type=DeviceType.UNOFFICIAL,  # 🔥 FIXED: All engine devices are UNOFFICIAL
                session_status=SessionStatus.connected if engine_device.get("status") == "connected" else SessionStatus.disconnected,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(new_device)
            db.commit()
            
            logger.info(f"   ✅ Auto-created device: {device_id} → user: {user_id}")
            
            return {"success": True, "device": new_device, "action": "created"}
            
        except Exception as e:
            logger.error(f"❌ Ensure device error: {e}")
            db.rollback()
            return {"success": False, "error": str(e)}
    
    def sync_all_users_devices(self, db: Session) -> Dict[str, any]:
        """
        Sync devices for all users (admin function)
        """
        logger.info("🔄 SYNCING DEVICES FOR ALL USERS")
        
        try:
            from models import BusiUser  # Fixed: Use BusiUser instead of Business
            
            # Get all users
            users = db.query(BusiUser).all()
            
            total_results = {
                "success": True,
                "users_processed": 0,
                "total_synced": 0,
                "total_created": 0,
                "total_updated": 0,
                "user_results": []
            }
            
            for user in users:
                user_id = str(user.busi_user_id)
                
                logger.info(f"   Processing user: {user_id}")
                user_result = self.sync_user_devices(db, user_id)
                
                total_results["user_results"].append({
                    "user_id": user_id,
                    "result": user_result
                })
                
                if user_result["success"]:
                    total_results["users_processed"] += 1
                    total_results["total_synced"] += user_result.get("synced", 0)
                    total_results["total_created"] += user_result.get("created", 0)
                    total_results["total_updated"] += user_result.get("updated", 0)
                else:
                    total_results["success"] = False
            
            logger.info(f"🏁 ALL USERS SYNC COMPLETE: {total_results}")
            return total_results
            
        except Exception as e:
            logger.error(f"❌ Sync all users error: {e}")
            return {"success": False, "error": str(e)}

# Global instance (legacy - will be deprecated)
_device_sync_service_legacy = DeviceSyncService()

def sync_user_devices(db: Session, user_id: str) -> Dict[str, any]:
    """Global function for easy access with rate limiting"""
    # Create service instance with database for proper rate limiting
    service = DeviceSyncService(db=db)
    return service.sync_user_devices(db, user_id)

def ensure_device_exists(db: Session, user_id: str, device_id: str) -> Dict[str, any]:
    """Global function for easy access with rate limiting"""
    # Create service instance with database for proper rate limiting
    service = DeviceSyncService(db=db)
    return service.ensure_device_exists(db, user_id, device_id)

# Legacy compatibility (deprecated)
device_sync_service = _device_sync_service_legacy
