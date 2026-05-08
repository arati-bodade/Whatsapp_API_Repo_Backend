#!/usr/bin/env python3
"""
🔥 DEVICE VALIDATOR - STEP 1: Device validation (MANDATORY)

On backend startup:
Call /health
Fetch /session/:id/status
Only keep CONNECTED device IDs
Disable invalid ones permanently
"""
import logging
import requests
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from models.device import Device
from core.config import settings

logger = logging.getLogger(__name__)

class DeviceValidator:
    """
    🔹 E. Stop Invalid Device Usage
    if engine_response.status_code == 404:
        mark_device_disabled(device_id)
        skip_trigger_for_device(device_id)
    """
    
    def __init__(self, engine_url: str = None):
        self.engine_url = engine_url or settings.WHATSAPP_ENGINE_BASE_URL
        self.session = requests.Session()
        
    def engine_is_healthy(self) -> bool:
        """Check if WhatsApp Engine is healthy"""
        try:
            response = self.session.get(f"{self.engine_url}/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Engine health check failed: {e}")
            return False
    
    def get_device_status(self, device_id: str) -> Optional[str]:
        """Get device session status from Engine"""
        try:
            response = self.session.get(f"{self.engine_url}/session/{device_id}/status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data.get("status", "unknown")
            elif response.status_code == 404:
                # Device not found in Engine
                return "not_found"
            else:
                logger.warning(f"Device {device_id} status check failed: HTTP {response.status_code}")
                return "error"
        except Exception as e:
            logger.error(f"Device status check failed for {device_id}: {e}")
            return "error"
    
    def validate_all_devices(self, db: Session) -> Dict[str, any]:
        """
        Validate all devices in database and disable invalid ones
        """
        logger.info("🔍 DEVICE VALIDATION: Starting device health check...")
        
        if not self.engine_is_healthy():
            logger.error("❌ Engine is not healthy - skipping device validation")
            return {
                "success": False,
                "error": "WhatsApp Engine is not healthy",
                "devices": []
            }
        
        # Get all devices from database
        devices = db.query(Device).all()
        
        validation_results = {
            "success": True,
            "engine_healthy": True,
            "devices": [],
            "connected_count": 0,
            "disabled_count": 0,
            "not_found_count": 0
        }
        
        logger.info(f"   Found {len(devices)} devices in database")
        
        for device in devices:
            device_status = self.get_device_status(device.device_id)
            
            device_result = {
                "device_id": device.device_id,
                "device_name": device.device_name,
                "engine_status": device_status,
                "db_status": device.session_status,
                "action": None
            }
            
            if device_status == "connected":
                # Device is healthy
                if device.session_status != "connected":
                    device.session_status = "connected"
                    device_result["action"] = "activated"
                    logger.info(f"   ✅ Device {device.device_id} activated")
                
                validation_results["connected_count"] += 1
                
            elif device_status == "not_found":
                # Device not found in Engine - disable permanently
                device.session_status = "expired"
                device_result["action"] = "disabled (not found)"
                validation_results["not_found_count"] += 1
                validation_results["disabled_count"] += 1
                
                logger.error(f"   ❌ Device {device.device_id} NOT FOUND in Engine - DISABLED")
                
            elif device_status in ["disconnected", "error"]:
                # Device is not connected - mark as inactive
                device.session_status = "disconnected"
                device_result["action"] = "marked inactive"
                validation_results["disabled_count"] += 1
                
                logger.warning(f"   ⚠️  Device {device.device_id} {device_status} - marked inactive")
                
            else:
                # Unknown status - mark as inactive
                device.session_status = "pending"
                device_result["action"] = f"marked inactive (unknown: {device_status})"
                validation_results["disabled_count"] += 1
                
                logger.warning(f"   ⚠️  Device {device.device_id} unknown status '{device_status}' - marked inactive")
            
            validation_results["devices"].append(device_result)
        
        # Commit all changes
        try:
            db.commit()
            logger.info(f"   ✅ Device validation complete: {validation_results['connected_count']} connected, {validation_results['disabled_count']} disabled")
        except Exception as e:
            logger.error(f"   ❌ Failed to commit device validation: {e}")
            db.rollback()
            validation_results["success"] = False
            validation_results["error"] = str(e)
        
        return validation_results
    
    def get_connected_devices(self, db: Session) -> List[Device]:
        """Get only connected/active devices"""
        return db.query(Device).filter(Device.session_status == "connected").all()
    
    def validate_device_before_send(self, db: Session, device_id: str, user_id: str = None) -> Dict[str, any]:
        """
        Validate a single device before sending message
        
        🔧 STEP 4: DEVICE VALIDATION LOGIC
        
        Modify device validation so:
        - Engine status is the source of truth
        - If engine reports "connected", device is valid
        - DB missing device should be auto-created, not rejected
        - Remove hard failures for temporary DB inconsistencies
        """
        # 🔥 BYPASS SQLAlchemy type coercion - use raw SQL text
        from sqlalchemy import text as sa_text
        device_id_str = str(device_id)
        raw_result = db.execute(
            sa_text("SELECT device_id FROM devices WHERE device_id::text = :did LIMIT 1"),
            {"did": device_id_str}
        ).fetchone()
        
        device = None
        if raw_result:
            device = db.query(Device).filter(
                sa_text("device_id::text = :did")
            ).params(did=device_id_str).first()
        
        # � PRODUCTION FIX: Auto-create missing device
        if not device and user_id:
            logger.info(f"   🆕 Device {device_id} not found in DB, auto-creating for user {user_id}")
            
            from services.device_sync_service import ensure_device_exists
            sync_result = ensure_device_exists(db, user_id, device_id)
            
            if sync_result["success"]:
                device = sync_result["device"]
                logger.info(f"   ✅ Auto-created device: {device_id}")
            else:
                return {
                    "valid": False,
                    "error": f"Device {device_id} not found and auto-creation failed: {sync_result.get('error')}"
                }
        
        if not device:
            return {
                "valid": False,
                "error": f"Device {device_id} not found in database"
            }
        
        # 🔥 FIX: Trust engine status over local enum
        # Check real-time status from Engine FIRST
        engine_status = self.get_device_status(device_id)
        
        if engine_status == "connected":
            # Engine says connected - trust it!
            # Update local status to match
            if device.session_status != "connected":
                device.session_status = "connected"
                db.commit()
                logger.info(f"   ✅ Device {device_id} status updated to connected")
            
            return {
                "valid": True,
                "device": device
            }
        
        elif engine_status == "not_found":
            # Device not found in Engine - disable permanently
            device.session_status = "expired"
            db.commit()
            
            return {
                "valid": False,
                "error": f"Device {device_id} not found in WhatsApp Engine (404)"
            }
        
        else:
            # Engine says disconnected/error - update local status
            device.session_status = "disconnected"
            db.commit()
            
            return {
                "valid": False,
                "error": f"Device {device_id} is not connected (engine status: {engine_status})"
            }
    
    def disable_invalid_triggers(self, db: Session):
        """
        Disable triggers that use invalid devices
        """
        from models.google_sheet import GoogleSheetTrigger
        
        logger.info("🔍 TRIGGER VALIDATION: Checking triggers for invalid devices...")
        
        # Get all triggers
        triggers = db.query(GoogleSheetTrigger).all()
        
        disabled_count = 0
        
        for trigger in triggers:
            device_validation = self.validate_device_before_send(db, trigger.device_id)
            
            if not device_validation["valid"]:
                # Disable this trigger
                trigger.is_enabled = False
                disabled_count += 1
                
                logger.warning(f"   ⚠️  Disabled trigger {trigger.trigger_id} - {device_validation['error']}")
        
        if disabled_count > 0:
            db.commit()
            logger.info(f"   ✅ Disabled {disabled_count} triggers with invalid devices")
        else:
            logger.info(f"   ✅ All triggers have valid devices")

# Global instance
device_validator = DeviceValidator()

def validate_all_devices(db: Session) -> Dict[str, any]:
    """Global function for easy access"""
    return device_validator.validate_all_devices(db)

def validate_device_before_send(db: Session, device_id: str, user_id: str = None) -> Dict[str, any]:
    """Global function for easy access"""
    return device_validator.validate_device_before_send(db, device_id, user_id)

def disable_invalid_triggers(db: Session):
    """Global function for easy access"""
    return device_validator.disable_invalid_triggers(db)
