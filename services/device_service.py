from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from models.device import Device, SessionStatus
from schemas.device import DeviceCreate, DeviceUpdate, DeviceRegisterRequest
from services.whatsapp_engine_service import WhatsAppEngineService
import qrcode
import io
import base64
import uuid
import os
import requests
from uuid import UUID
import logging
from services.uuid_service import UUIDService

logger = logging.getLogger(__name__)


class DeviceService:
    def __init__(self, db: Session):
        self.db = db

    def create_device(self, device_data: DeviceCreate) -> Device:
        """Create a new device"""
        if not device_data.device_id:
            device_data.device_id = f"device-{uuid.uuid4().hex[:8]}"
        
        db_device = Device(**device_data.model_dump())
        self.db.add(db_device)
        self.db.commit()
        self.db.refresh(db_device)
        return db_device

    def register_device(self, user_id: str, device_request: DeviceRegisterRequest) -> Device:
        """Register a new device for WhatsApp Web (unofficial) - MULTIPLE DEVICES ALLOWED"""
        from models.device import DeviceType
        from models.busi_user import BusiUser
        
        logger.info(f"🔧 DEVICE REGISTRATION STARTED - User: {user_id}, Device Name: {device_request.device_name}, Type: {device_request.device_type}")
        
        # 🔥 STEP 1: Device limit check removed - unlimited devices allowed
        # 🔥 STEP 1: Identify User Role and Existence
        # Check BusiUser first (most common)
        user = self.db.query(BusiUser).filter(BusiUser.busi_user_id == str(user_id)).first()
        user_role = "business" if user else None
        
        # If not found, check Reseller
        if not user:
            from models.reseller import Reseller
            user = self.db.query(Reseller).filter(Reseller.reseller_id == str(user_id)).first()
            user_role = "reseller" if user else None
            
        # If still not found, check MasterAdmin
        if not user:
            from models.admin import MasterAdmin
            user = self.db.query(MasterAdmin).filter(MasterAdmin.admin_id == str(user_id)).first()
            user_role = "admin" if user else None
            
        if not user:
            logger.error(f"❌ User {user_id} not found in any user table (BusiUser, Reseller, Admin)")
            raise ValueError(f"User {user_id} not found during device registration")
        
        logger.info(f"👤 User Role Detected: {user_role} - Unlimited devices enabled for all authorized roles")
        
        # Device limit check removed - users can now add unlimited devices
        
        # 🔥 STEP 2: Handle Official Device Duplicates and Name Collisions
        # Check if a device (active or deleted) with the SAME NAME already exists for this user
        # This prevents (psycopg2.errors.UniqueViolation) on uniq_user_device_name
        existing_with_name = self.db.query(Device).filter(
            Device.busi_user_id == str(user_id),
            Device.device_name == device_request.device_name
        ).first()

        if existing_with_name:
            if existing_with_name.is_active and existing_with_name.deleted_at is None:
                # If it's active and official, only one allowed
                if device_request.device_type == DeviceType.official:
                    logger.warning(f"🚨 Official device already exists and is active for user {user_id}")
                    raise ValueError("An official WhatsApp device is already registered for this user.")
                # For others, we might allow multiple? No, the constraint is on name.
                logger.warning(f"🚨 Device with name '{device_request.device_name}' already exists and is active.")
                raise ValueError(f"A device with the name '{device_request.device_name}' already exists.")
            else:
                # It exists but IS DELETED - Re-activate it!
                logger.info(f"♻️ Re-activating deleted device '{device_request.device_name}' for user {user_id}")
                existing_with_name.is_active = True
                existing_with_name.deleted_at = None
                existing_with_name.session_status = SessionStatus.created
                existing_with_name.device_type = device_request.device_type # Update type if requested
                existing_with_name.last_active = datetime.now(timezone.utc)
                self.db.commit()
                self.db.refresh(existing_with_name)
                return existing_with_name
        
        # 🔥 STEP 3: Handle Multi-Device for Unofficial Devices (Max 5 limit)
        if device_request.device_type != DeviceType.official:
            active_unofficial_count = self.db.query(Device).filter(
                Device.busi_user_id == str(user_id),
                Device.device_type == device_request.device_type,
                Device.deleted_at.is_(None)
            ).count()
            
            if active_unofficial_count >= 5:
                logger.warning(f"🚨 Max devices limit reached for user {user_id} ({active_unofficial_count} devices)")
                raise ValueError("Maximum limit of 5 unofficial devices reached. Please delete an existing device first.")

        # Create new device if no conflict found
        device_id = str(uuid.uuid4())
        logger.info(f"🆔 Generating new device ID: {device_id}")
        
        device_data = DeviceCreate(
            device_id=device_id,
            busi_user_id=str(user_id),
            device_name=device_request.device_name,
            device_type=device_request.device_type,  # Use requested device type
            session_status=SessionStatus.created,  # Start with created status - NO AUTO-CONNECT
            qr_last_generated=None, # No QR yet
            last_active=datetime.now(timezone.utc),
            is_active=True  # Device should be visible immediately
        )
        
        device = self.create_device(device_data)
        logger.info(f"✅ DEVICE REGISTRATION SUCCESS - ID: {device.device_id}, Name: {device.device_name}, Type: {device.device_type}, Status: {device.session_status}")
        return device

    def get_device_by_id(self, device_id: str) -> Optional[Device]:
        """Get device by ID (accepts string UUID)"""
        # ✅ Use centralized UUID service for consistent handling
        device_uuid = UUIDService.safe_convert(device_id)
        return self.db.query(Device).filter(Device.device_id == str(device_uuid)).first()

    def get_devices_by_user(
        self, 
        user_id: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Device]:
        """Get devices for a specific user with pagination."""
        user_uuid = UUIDService.safe_convert(user_id)
        return (
            self.db.query(Device)
            .filter(
                Device.busi_user_id == str(user_uuid),
                Device.deleted_at.is_(None)
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_user_devices(
        self, 
        user_id: str, 
        session_status: Optional[str] = None
    ) -> List[Device]:
        """Get devices for a user, optionally filtered by session status"""
        from uuid import UUID
        from services.uuid_service import UUIDService
        
        # Convert string UUID to UUID object
        user_uuid = UUIDService.safe_convert(user_id)
        
        query = self.db.query(Device).filter(
            Device.busi_user_id == str(user_uuid),
            Device.deleted_at.is_(None)
        )
        
        if session_status:
            query = query.filter(Device.session_status == session_status)
            
        return query.all()

    def get_connected_devices(self, user_id: str) -> List[Device]:
        """Get all connected devices for a user"""
        user_uuid = UUIDService.safe_convert(user_id)
        return (
            self.db.query(Device)
            .filter(
                Device.busi_user_id == str(user_uuid),
                Device.session_status == "connected",
                Device.is_active.is_(True)
            )
            .all()
        )

    def is_device_connected(self, device_id: str) -> bool:
        """Check if a device is connected according to the database"""
        device_uuid = UUIDService.safe_convert(device_id)
        device = self.db.query(Device).filter(Device.device_id == str(device_uuid)).first()
        if not device:
            return False
        
        try:
            # Handle both enum and string safely
            status_val = getattr(device.session_status, 'value', device.session_status)
            return status_val == "connected"
        except Exception as e:
            logger.error(f"Error checking device connected status: {e}")
            return False


    def update_device_status(
        self, 
        device_id: str, 
        session_status: str,  # Changed to accept string
        ip_address: Optional[str] = None
    ) -> Optional[Device]:
        """Update device session status"""
        # ✅ Use centralized UUID service for consistent handling
        device_uuid = UUIDService.safe_convert(device_id)
        device = self.db.query(Device).filter(Device.device_id == str(device_uuid)).first()
        if device:
            # Convert string to SessionStatus enum
            try:
                from models.device import SessionStatus
                device.session_status = SessionStatus(session_status)
            except ValueError:
                # If invalid status, use a default
                logger.warning(f"Invalid session status '{session_status}' for device {device_id}, using 'pending'")
                device.session_status = SessionStatus.pending
            
            device.last_active = datetime.now(timezone.utc)
            if ip_address:
                device.ip_address = ip_address
            self.db.commit()
            self.db.refresh(device)
        return device

    def update_device(
        self, 
        device_id: str, 
        update_data: DeviceUpdate
    ) -> Optional[Device]:
        """Update device details"""
        # ✅ Use centralized UUID service for consistent handling
        device_uuid = UUIDService.safe_convert(device_id)
        device = self.db.query(Device).filter(Device.device_id == str(device_uuid)).first()
        if device:
            for field, value in update_data.model_dump(exclude_unset=True).items():
                setattr(device, field, value)
            self.db.commit()
            self.db.refresh(device)
        return device

    def generate_qr_code(self, device_id: str) -> Optional[Device]:
        """Generate/Fetch QR code for device from Engine - NO COOLDOWN"""
        # ✅ Use centralized UUID service
        device_uuid = UUIDService.safe_convert(device_id)
        device = self.db.query(Device).filter(Device.device_id == str(device_uuid)).first()
        
        if device:
            # 🔥 STRICT SEPARATION: Official devices NEVER get QR codes
            from models.device import DeviceType
            if device.device_type == DeviceType.official:
                raise ValueError("OFFICIAL_DEVICE_NO_QR")

            # 🔥 REMOVED COOLDOWN CHECK (REQUIREMENT 4)
            # We want QR to always be available if requested

            # 1. Initialize Engine Service
            engine_service = WhatsAppEngineService(self.db)
            
            # 2. Request QR from Engine (this initiates session if needed)
            logger.info(f"Requesting QR from engine for {device_id}")
            
            # 🔥 Convert to string explicitly
            device_id_str = str(device.device_id)
            result = engine_service.get_qr_code(device_id_str)
            
            # 🔥 Handle Engine Service responses properly
            if not result.get("success"):
                error_msg = result.get("error", "Unknown engine error")
                
                # If engine returns retry_after, we just log it but don't block
                if "retry_after" in result:
                    logger.info(f"Engine suggested retry after {result['retry_after']}s, but we continue polling")
                
                logger.error(f"Failed to get QR check: {error_msg}")
                
                # 🔥 AUTO-HEAL: If engine session doesn't exist, start it!
                if "not found" in error_msg.lower():
                    logger.warning(f"🚨 Session {device_id_str} missing in Engine! Auto-starting...")
                    
                    try:
                        self.start_device(device_id_str)
                        device.session_status = SessionStatus.created
                        self.db.commit()
                        self.db.refresh(device)
                    except Exception as e:
                        logger.error(f"Auto-heal start failed: {e}")
                
                # Don't raise error, just return None so frontend keeps polling
                # raise RuntimeError(f"ENGINE_ERROR:{error_msg}")
                return device
            
            # If success, process data
            if result.get("success"):
                data = result.get("data", {})
                status = data.get("status")
                
                logger.info(f"Engine returned status for {device_id}: {status}")

                # 🔥 FIXED: Handle ALREADY CONNECTED without error
                if status == "connected" or status == "authenticated":
                    # While engine says connected, we SHOULD trust it
                    device.session_status = SessionStatus.connected
                    device.qr_code = None # Clear QR if connected
                    device.last_active = datetime.now(timezone.utc)
                    self.db.commit()
                    self.db.refresh(device)
                    logger.info(f"Device {device_id} is verified connected by engine (no QR needed)")
                    return device # Return early as success
                    
                # 🔥 CRITICAL FIX: qr/qr_ready should NOT mark as connected!
                if status == "qr_ready" or status == "qr":
                    qr_base64 = data.get("qr")
                    if qr_base64:
                        # Engine returns raw base64 usually, ensure data URI format
                        if not qr_base64.startswith("data:"):
                            device.qr_code = f"data:image/png;base64,{qr_base64}"
                        else:
                            device.qr_code = qr_base64
                            
                        # 🔥 FIXED: Set status to qr_ready, NOT connected!
                        device.session_status = SessionStatus.qr_ready
                        device.qr_last_generated = datetime.now(timezone.utc)
                        logger.info(f"✅ QR code ready for {device_id} - WAITING FOR SCAN")
                    else:
                        logger.warning(f"Engine reported qr_ready but no QR data for {device_id}")
                        # Keep as created/qr_ready but don't set connected
                        device.session_status = SessionStatus.qr_ready
                
                elif status == "authenticated":
                     # Engine 'authenticated' maps to 'connected'
                    device.session_status = SessionStatus.connected
                    device.qr_code = None
                    device.last_active = datetime.now(timezone.utc)
                    logger.info(f"Device {device_id} is authenticated (connected)")

                elif status == "pending" or status == "generating":
                    # Keep status as is or set to created
                    logger.info(f"QR code is pending for {device_id}")
                    # Ensure status is at least created/qr_ready so it shows up
                    if device.session_status not in [SessionStatus.qr_ready, SessionStatus.connected]:
                        device.session_status = SessionStatus.created
                    # explicitly clear any stale QR code to prevent placeholders
                    device.qr_code = None
                    pass 
                    
                self.db.commit()
                self.db.refresh(device)
            else:
                logger.error(f"Failed to get QR from engine for {device_id}: {result.get('error')}")
                
        return device

    def disconnect_device(self, device_id: str) -> Optional[Device]:
        """Disconnect a device"""
        return self.update_device_status(device_id, "disconnected")

    def start_device(self, device_id: str) -> Dict[str, Any]:
        """Manually start a device session and transition cleanly"""
        logger.info(f"Starting device initialization for {device_id}")
        device_uuid = UUIDService.safe_convert(device_id)
        device = self.db.query(Device).filter(Device.device_id == str(device_uuid)).first()
        
        if not device:
            return {"success": False, "error": "device_not_found"}
        
        engine_service = WhatsAppEngineService(self.db)
        result = engine_service.start_session(str(device_id))
        
        if result.get("success"):
            device.session_status = SessionStatus.created
            device.qr_code = None
            device.last_active = datetime.now(timezone.utc)
            self.db.commit()
            
        return result

    def logout_device(self, device_id: str) -> Dict[str, Any]:
        """Logout device with immediate session cleanup and proper lifecycle management"""
        logger.info(f"🔥 Starting IMMEDIATE logout process for device {device_id}")
        
        device = self.get_device_by_id(device_id)
        if not device:
            logger.info(f"Device {device_id} not found in database")
            return {"success": False, "error": "device_not_found"}
        
        # Check if device is already logged out
        from models.device import SessionStatus
        
        # Force continue even if status is logged_out, to ensure is_active is False
        if device.session_status == SessionStatus.logged_out and not device.is_active:
             logger.info(f"Device {device_id} is already logged out and inactive")
             return {"success": True, "status": "already_logged_out"}

        try:
            # 🔥 STEP 1: IMMEDIATE DB STATUS UPDATE (happens first)
            logger.info(f"Step 1: IMMEDIATE DB status update for device {device_id}")
            device.session_status = SessionStatus.logged_out
            device.is_active = False # 🔥 REQUIREMENT 7: Logout means Device disappears from UI (Soft Delete)
            device.disconnected_at = datetime.now(timezone.utc)  # Track when logout happened
            device.deleted_at = datetime.now(timezone.utc)  # 🔥 ADDED: Permanent deletion flag
            device.last_active = datetime.now(timezone.utc)
            self.db.commit()
            logger.info(f"✅ Device {device_id} immediately marked as logged_out and inactive")
            
            # 🔥 STEP 2: Engine session cleanup (async, doesn't block response)
            logger.info(f"Step 2: Engine session cleanup for device {device_id}")
            try:
                engine_service = WhatsAppEngineService(self.db)
                engine_result = engine_service.delete_session(str(device_id))
                
                engine_success = engine_result.get("success", False)
                if engine_success:
                    logger.info(f"✅ Engine session deleted for device {device_id}")
                else:
                    logger.warning(f"⚠️ Engine logout failed for device {device_id}: {engine_result.get('error')}")
                    # Continue - DB already updated, so logout is still successful
            except Exception as engine_error:
                logger.error(f"⚠️ Engine logout exception for device {device_id}: {str(engine_error)}")
                # Continue - DB already updated, so logout is still successful
            
            # 🔥 NOTE: We intentionally removed the "history preserved" check.
            # Requirement 7: "Logged-out devices must NEVER appear again"
            # References in Inbox/Sheets will point to this device_id which still exists in DB rows
            # but is marked is_active=False, so it won't show up in lists.
            
            # 🔥 STEP 4: Return immediate success (logout already complete)
            logger.info(f"✅ Logout completed successfully for device {device_id}")
            return {"success": True, "status": "logged_out"}
                
        except Exception as e:
            logger.error(f"❌ Error during logout for device {device_id}: {str(e)}")
            try:
                self.db.rollback()
            except:
                pass
            return {"success": False, "error": "internal_error"}
    
    def delete_device(self, device_id: str) -> bool:
        """Legacy delete method - use logout_device instead"""
        logger.warning(f"Using legacy delete_device for {device_id} - consider using logout_device")
        result = self.logout_device(device_id)
        return result.get("success", False)

    def sync_device_status_from_engine(self, device_id: str) -> Dict[str, Any]:
        """Sync device status from engine and update database"""
        try:
            engine_service = WhatsAppEngineService(self.db)
            
            # Get status from engine
            status_result = engine_service.check_device_status(device_id)
            
            if not status_result.get("success"):
                return {"success": False, "error": "Failed to check engine status"}
            
            engine_status = status_result.get("status", "unknown")
            
            # Map engine status to database status
            status_mapping = {
                "connected": SessionStatus.connected,
                "disconnected": SessionStatus.disconnected,
                "qr": SessionStatus.qr_ready,
                "qr_ready": SessionStatus.qr_ready,
                "generating": SessionStatus.created,
                "pending": SessionStatus.created
            }
            
            new_status = status_mapping.get(engine_status, SessionStatus.disconnected)
            
            # Update device in database
            device_uuid = UUIDService.safe_convert(device_id)
            device = self.db.query(Device).filter(Device.device_id == str(device_uuid)).first()
            if not device:
                return {"success": False, "error": "Device not found"}
            
            old_status = device.session_status
            device.session_status = new_status
            device.last_active = datetime.now(timezone.utc)
            
            # If device became connected, clear QR cache
            if new_status == SessionStatus.connected:
                if hasattr(engine_service, '_qr_cache') and device_id in engine_service._qr_cache:
                    del engine_service._qr_cache[device_id]
                    logger.info(f"🗑️ Cleared QR cache for connected device {device_id}")
            
            self.db.commit()
            
            logger.info(f"🔄 Device {device_id} status synced: {old_status} → {new_status} (engine: {engine_status})")
            
            return {
                "success": True,
                "old_status": old_status.value if old_status else None,
                "new_status": new_status.value,
                "engine_status": engine_status
            }
            
        except Exception as e:
            logger.error(f"❌ Error syncing device status for {device_id}: {str(e)}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    def get_device_with_sync(self, device_id: str) -> Optional[Device]:
        """Get device with automatic status sync from engine"""
        device = self.get_device_by_id(device_id)
        if device:
            # Sync status from engine to ensure consistency
            sync_result = self.sync_device_status_from_engine(device_id)
            if sync_result.get("success"):
                # Refresh device to get updated status
                self.db.refresh(device)
        return device

    def get_device_count(self, user_id: str) -> int:
        """Get total device count for a user"""
        user_uuid = UUIDService.safe_convert(user_id)
        return (
            self.db.query(Device)
            .filter(
                Device.busi_user_id == str(user_uuid), 
                Device.is_active.is_(True)
            )
            .count()
        )

    def get_device_count_by_user(self, user_id: str) -> int:
        """Alias for get_device_count to maintain API compatibility"""
        return self.get_device_count(user_id)

    def count_devices_by_user(self, user_id: str) -> int:
        """Missing attribute fix: Alias for get_device_count"""
        return self.get_device_count(user_id)

    def cleanup_expired_devices(self, hours: int = 24) -> int:
        """Clean up devices that have been inactive for specified hours"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        expired_devices = (
            self.db.query(Device)
            .filter(
                Device.last_active < cutoff_time,
                Device.session_status.in_(["disconnected", "expired"]),
                Device.is_active.is_(True)
            )
            .all()
        )
        
        count = len(expired_devices)
        for device in expired_devices:
            # self.db.delete(device) # Don't hard delete
            device.is_active = False 
            device.session_status = "expired"
        
        self.db.commit()
        return count
    
    def heal_orphaned_devices(self) -> int:
        """
        Auto-heal orphaned devices by:
        1. Checking DB-active devices against Engine (mark missing ones as orphaned)
        2. Checking Engine sessions against DB (cleanup sessions for deleted/missing DB devices)
        """
        from models.device import SessionStatus
        
        engine_service = WhatsAppEngineService(self.db)
        healed_count = 0
        
        # 🔥 STEP 1: DB → ENGINE (Already exists, but improved)
        active_devices = (
            self.db.query(Device)
            .filter(
                Device.session_status.in_([SessionStatus.connected, SessionStatus.qr_ready]),
                Device.is_active.is_(True),
                Device.deleted_at.is_(None)
            )
            .all()
        )
        
        for device in active_devices:
            try:
                engine_status = engine_service.check_device_status(str(device.device_id))
                if engine_status.get("status") == "not_found":
                    device.session_status = SessionStatus.orphaned
                    healed_count += 1
                    logger.info(f"📍 Device {device.device_id} marked as orphaned (missing in engine)")
            except Exception as e:
                logger.error(f"⚠️ Error checking device {device.device_id}: {e}")
        
        # 🔥 STEP 2: ENGINE → DB (Cleanup stale sessions in engine)
        # This solves the "Engine shows Connected but UI shows nothing" problem
        try:
            # Fetch all sessions directly from engine
            engine_url = os.getenv("WHATSAPP_ENGINE_URL", "http://localhost:3002")
            response = requests.get(f"{engine_url}/sessions", timeout=5)
            
            if response.status_code == 200:
                engine_sessions = response.json()
                for device_id_str, session_info in engine_sessions.items():
                    # For each session in engine, check its status in DB
                    device_uuid = UUIDService.safe_convert(device_id_str)
                    db_device = self.db.query(Device).filter(Device.device_id == str(device_uuid)).first()
                    
                    # If device is missing from DB or is soft-deleted (deleted_at is set)
                    if not db_device or db_device.deleted_at is not None or not db_device.is_active:
                        logger.warning(f"🧹 Found stale engine session for deleted/missing device {device_id_str}. Cleaning up engine...")
                        try:
                            engine_service.delete_session(device_id_str)
                            healed_count += 1
                        except Exception as del_err:
                            logger.error(f"Failed to delete stale engine session {device_id_str}: {del_err}")
                            
            self.db.commit()
        except Exception as e:
            logger.error(f"⚠️ Failed to perform Engine → DB sync in heal: {e}")
            
        return healed_count
    
    # 🔥 NEW METHODS FOR DEVICE TYPE FILTERING
    def get_devices_by_user_and_type(self, user_id: str, device_type, skip: int = 0, limit: int = 100) -> List[Device]:
        """Get devices for a user filtered by device_type with minimal filtering"""
        from models.device import DeviceType
        user_uuid = UUIDService.safe_convert(user_id)
        
        query = (
            self.db.query(Device)
            .filter(
                Device.busi_user_id == str(user_uuid),
                Device.device_type == device_type,
                Device.deleted_at.is_(None)  # 🔥 REQUIRED: Filter by deleted_at
            )
            .order_by(Device.last_active.desc().nullslast())
        )
        
        devices = query.offset(skip).limit(limit).all()
        logger.info(f"Found {len(devices)} {device_type} devices for user {user_id}")
        
        # 🔥 SPECIAL HANDLING: For official devices, ensure only one per user
        if device_type == DeviceType.official and len(devices) > 1:
            logger.warning(f"🚨 Found {len(devices)} official devices for user {user_id}, deduplicating...")
            # Sort by last_active and created_at to get the most recent one
            devices.sort(key=lambda d: (d.last_active or d.created_at, d.created_at), reverse=True)
            # Return only the most recent official device
            latest_device = devices[0]
            logger.info(f"✅ Returning most recent official device: {latest_device.device_id} (created: {latest_device.created_at})")
            return [latest_device]
        
        return devices
    
    def count_devices_by_user_and_type(self, user_id: str, device_type) -> int:
        """Count devices for a user filtered by device_type with minimal filtering"""
        from models.device import DeviceType
        user_uuid = UUIDService.safe_convert(user_id)
        
        count = (
            self.db.query(Device)
            .filter(
                Device.busi_user_id == str(user_uuid),
                Device.device_type == device_type,
                Device.deleted_at.is_(None)  # 🔥 REQUIRED: Filter by deleted_at
            )
            .count()
        )
        
        # 🔥 SPECIAL HANDLING: For official devices, count as max 1 per user
        if device_type == DeviceType.official and count > 1:
            logger.info(f"🚨 Found {count} official devices for user {user_id}, counting as 1")
            return 1
        
        logger.info(f"Counted {count} {device_type} devices for user {user_id}")
        return count
    
    def cleanup_duplicate_official_devices(self, user_id: str) -> Dict[str, Any]:
        """Clean up duplicate official devices, keeping only the most recent one"""
        from models.device import DeviceType
        user_uuid = UUIDService.safe_convert(user_id)
        
        try:
            # Get all official devices for the user
            official_devices = self.db.query(Device).filter(
                Device.busi_user_id == str(user_uuid),
                Device.device_type == DeviceType.official,
                Device.deleted_at.is_(None)
            ).all()
            
            if len(official_devices) <= 1:
                return {
                    "success": True,
                    "cleaned_count": 0,
                    "message": "No duplicate official devices found"
                }
            
            logger.warning(f"🧹 Cleaning up {len(official_devices)} official devices for user {user_id}")
            
            # Sort by last_active and created_at to find the most recent one
            official_devices.sort(key=lambda d: (d.last_active or d.created_at, d.created_at), reverse=True)
            
            # Keep the first (most recent) device, mark others as deleted
            device_to_keep = official_devices[0]
            devices_to_delete = official_devices[1:]
            
            cleaned_count = 0
            for device in devices_to_delete:
                logger.info(f"🗑️ Marking duplicate official device as deleted: {device.device_id}")
                device.deleted_at = datetime.now(timezone.utc)
                cleaned_count += 1
            
            self.db.commit()
            
            return {
                "success": True,
                "cleaned_count": cleaned_count,
                "kept_device_id": str(device_to_keep.device_id),
                "message": f"Cleaned up {cleaned_count} duplicate official devices, kept most recent: {device_to_keep.device_id}"
            }
            
        except Exception as e:
            logger.error(f"❌ Error cleaning up duplicate official devices: {e}")
            self.db.rollback()
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to clean up duplicate official devices"
            }
