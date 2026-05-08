#!/usr/bin/env python3
"""
🔥 DEVICE MONITOR SERVICE - Continuous Connection Stability Monitor

This service runs in the background to ensure device connections remain stable.
It proactively monitors device health and attempts automatic recovery when connections drop.

Key Features:
- Continuous monitoring of all active devices
- Automatic reconnection attempts for dropped connections
- Health checks with configurable intervals
- Graceful handling of engine connectivity issues
- Detailed logging for troubleshooting
"""

import logging
import asyncio
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from models.device import Device, SessionStatus
from services.device_sync_service import device_sync_service
from services.whatsapp_engine_service import WhatsAppEngineService
from core.config import settings

logger = logging.getLogger(__name__)

class DeviceMonitorService:
    """
    Background service for continuous device monitoring and automatic recovery
    """
    
    def __init__(self, db_session_factory=None):
        self.db_session_factory = db_session_factory
        self.monitoring_active = False
        self.monitor_thread = None
        self.monitor_interval = 60  # 🔥 INCREASED: 60 seconds to prevent rapid loops
        self.health_check_interval = 120  # 🔥 INCREASED: 2 minutes between health checks
        self.max_recovery_attempts = 2  # 🔥 REDUCED: Max 2 auto-recovery attempts per device
        self.recovery_cooldown = 600  # 🔥 INCREASED: 10 minutes between recovery attempts
        
        # Track recovery attempts per device
        self.recovery_attempts = {}  # {device_id: {"count": int, "last_attempt": datetime}}
        
    def start_monitoring(self):
        """Start the background monitoring thread"""
        if self.monitoring_active:
            logger.warning("Device monitoring is already active")
            return
            
        logger.info("🚀 Starting device monitoring service")
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
    def stop_monitoring(self):
        """Stop the background monitoring thread"""
        logger.info("🛑 Stopping device monitoring service")
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=10)
            
    def _monitor_loop(self):
        """Main monitoring loop running in background thread"""
        logger.info("📡 Device monitoring loop started")
        
        while self.monitoring_active:
            try:
                with self.db_session_factory() as db:
                    self._monitor_devices(db)
                    
                # Sleep between monitoring cycles
                time.sleep(self.monitor_interval)
                
            except Exception as e:
                logger.error(f"❌ Error in monitoring loop: {e}")
                time.sleep(self.monitor_interval)  # Continue even if error occurs
                
        logger.info("📡 Device monitoring loop stopped")
        
    def _monitor_devices(self, db: Session):
        """
        Monitor all active devices and attempt recovery for disconnected ones
        🔥 FIXED: Prevent infinite reconnection loops
        """
        try:
            # Get all active devices (excluding official devices)
            active_devices = db.query(Device).filter(
                Device.is_active.is_(True),
                Device.deleted_at.is_(None),
                Device.device_type != 'official'
            ).all()
            
            if not active_devices:
                return
                
            logger.debug(f"🔍 Monitoring {len(active_devices)} active devices")
            
            engine_service = WhatsAppEngineService(db)
            connected_count = 0
            recovered_count = 0
            
            for device in active_devices:
                try:
                    # 🔥 FIXED: Check if device was recently updated to avoid loops
                    now = datetime.now(timezone.utc)
                    if device.updated_at:
                        time_since_update = (now - device.updated_at).total_seconds()
                        # Skip monitoring if device was updated within last 30 seconds
                        if time_since_update < 30:
                            logger.debug(f"⏭️ Skipping device {device.device_name} - updated {time_since_update}s ago")
                            continue
                    
                    # Check current device status in engine
                    engine_status = engine_service.check_device_status(str(device.device_id))
                    engine_status_value = engine_status.get("status", "unknown")
                    
                    # Map engine status to database status
                    if engine_status_value == "connected":
                        if device.session_status != SessionStatus.connected:
                            device.session_status = SessionStatus.connected
                            device.last_active = now
                            device.updated_at = now
                            logger.info(f"✅ Device {device.device_name} connected")
                        connected_count += 1
                        
                    elif engine_status_value in ["disconnected", "not_found"]:
                        # 🔥 FIXED: Only attempt recovery if device was recently connected
                        if device.session_status == SessionStatus.connected:
                            if device.last_active:
                                time_since_active = (now - device.last_active).total_seconds()
                                # Only recover if device was active within last 2 minutes
                                if time_since_active < 120:
                                    if self._should_attempt_recovery(device):
                                        recovery_success = self._attempt_device_recovery(device, engine_service)
                                        if recovery_success:
                                            recovered_count += 1
                                            # Mark as connecting to prevent immediate re-check
                                            device.session_status = SessionStatus.connecting
                                            device.updated_at = now
                                else:
                                    logger.warning(f"⏸️ Device {device.device_name} disconnected too long ago ({time_since_active}s) - skipping recovery")
                            else:
                                # Mark as disconnected
                                device.session_status = SessionStatus.disconnected
                                device.updated_at = now
                        
                    elif engine_status_value == "qr_ready":
                        if device.session_status != SessionStatus.qr_ready:
                            device.session_status = SessionStatus.qr_ready
                            device.updated_at = now
                            logger.info(f"📱 Device {device.device_name} ready for QR")
                            
                    # Update timestamp
                    device.updated_at = now
                    
                except Exception as device_error:
                    logger.warning(f"⚠️ Error monitoring device {device.device_id}: {device_error}")
                    continue
                    
            # Commit all status updates
            db.commit()
            
            if connected_count > 0 or recovered_count > 0:
                logger.info(f"📊 Monitoring cycle: {connected_count} connected, {recovered_count} recovered")
                
        except Exception as e:
            logger.error(f"❌ Error in device monitoring: {e}")
            db.rollback()
            
    def _should_attempt_recovery(self, device: Device) -> bool:
        """
        Check if we should attempt recovery for this device
        """
        device_id = str(device.device_id)
        now = datetime.now(timezone.utc)
        
        # Get recovery tracking for this device
        recovery_info = self.recovery_attempts.get(device_id, {"count": 0, "last_attempt": None})
        
        # Check if we've exceeded max attempts
        if recovery_info["count"] >= self.max_recovery_attempts:
            # Reset counter if enough time has passed (24 hours)
            if recovery_info["last_attempt"] and (now - recovery_info["last_attempt"]).total_seconds() > 86400:
                recovery_info["count"] = 0
                recovery_info["last_attempt"] = None
            else:
                return False
                
        # Check cooldown period
        if recovery_info["last_attempt"]:
            time_since_last = (now - recovery_info["last_attempt"]).total_seconds()
            if time_since_last < self.recovery_cooldown:
                return False
                
        # Only attempt recovery for devices that were recently connected
        if device.last_active:
            time_since_active = (now - device.last_active).total_seconds()
            # Only recover if device was active within the last hour
            if time_since_active > 3600:
                return False
                
        return True
        
    def _attempt_device_recovery(self, device: Device, engine_service: WhatsAppEngineService) -> bool:
        """
        Attempt to recover a disconnected device
        """
        device_id = str(device.device_id)
        logger.info(f"🔄 Attempting recovery for device {device.device_name} ({device_id})")
        
        try:
            # Update recovery tracking
            now = datetime.now(timezone.utc)
            recovery_info = self.recovery_attempts.get(device_id, {"count": 0, "last_attempt": None})
            recovery_info["count"] += 1
            recovery_info["last_attempt"] = now
            self.recovery_attempts[device_id] = recovery_info
            
            # Attempt reconnection
            reconnect_result = engine_service.reconnect_device(device_id)
            
            if reconnect_result.get("success"):
                logger.info(f"✅ Recovery initiated for device {device.device_name}")
                
                # Mark device as connecting
                device.session_status = SessionStatus.connecting
                device.last_active = now
                return True
            else:
                logger.warning(f"⚠️ Recovery failed for device {device.device_name}: {reconnect_result.get('error')}")
                return False
                
        except Exception as recovery_error:
            logger.error(f"❌ Recovery error for device {device.device_name}: {recovery_error}")
            return False
            
    def force_sync_all_devices(self) -> Dict[str, Any]:
        """
        Force immediate sync of all devices (manual trigger)
        🔥 FIXED: Prevent errors and infinite loops
        """
        logger.info("🔄 Force syncing all devices")
        
        try:
            with self.db_session_factory() as db:
                # Get all users with devices
                from models.busi_user import BusiUser
                users_with_devices = db.query(Device.busi_user_id).distinct().all()
                user_ids = [str(user[0]) for user in users_with_devices]
                
                total_synced = 0
                total_updated = 0
                total_created = 0
                
                for user_id in user_ids:
                    try:
                        sync_result = device_sync_service.sync_user_devices(db, user_id)
                        if sync_result.get("success"):
                            total_synced += sync_result.get("synced", 0)
                            total_updated += sync_result.get("updated", 0)
                            total_created += sync_result.get("created", 0)
                    except Exception as user_error:
                        logger.warning(f"⚠️ Failed to sync devices for user {user_id}: {user_error}")
                        
                db.commit()
                
                result = {
                    "success": True,
                    "users_processed": len(user_ids),
                    "total_synced": total_synced,
                    "total_updated": total_updated,
                    "total_created": total_created
                }
                
                logger.info(f"✅ Force sync complete: {result}")
                return result
                
        except Exception as e:
            logger.error(f"❌ Force sync failed: {e}")
            return {"success": False, "error": str(e)}

# Global instance
device_monitor_service = DeviceMonitorService()

def start_device_monitoring():
    """Start the global device monitoring service"""
    device_monitor_service.start_monitoring()

def stop_device_monitoring():
    """Stop the global device monitoring service"""
    device_monitor_service.stop_monitoring()
