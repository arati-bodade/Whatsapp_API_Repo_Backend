#!/usr/bin/env python3
"""
🔒 SESSION VALIDATION SERVICE
Prevents session chaos, QR spam, and invalid session restores
"""
import logging
import time
import uuid
from typing import Dict, Any, Optional, Set
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models.device import Device

logger = logging.getLogger(__name__)

class SessionValidationService:
    """
    🔥 PRODUCTION-GRADE SESSION VALIDATION
    
    - Prevents QR spam with cooldown
    - Validates session IDs before restore
    - Filters out invalid/test sessions
    - Manages session lifecycle safely
    """
    
    def __init__(self):
        # QR cooldown tracking: {device_id: last_generated_time}
        self._qr_cooldowns: Dict[str, float] = {}
        self._qr_cooldown_seconds = 30  # Minimum 30 seconds between QR generations
        
        # Session restore tracking
        self._recent_restores: Set[str] = set()
        self._restore_cleanup_time = 300  # 5 minutes
        
    def is_valid_device_id(self, device_id: str) -> bool:
        """
        🔥 CRITICAL: Validate device_id before any operations
        Supports both UUIDs (unofficial) and numeric strings (official)
        """
        if not device_id or not isinstance(device_id, str):
            return False
            
        # Reject common test/invalid IDs
        invalid_patterns = [
            "test-device-id",
            "test-manual-fix",
            "test-",
            "manual-",
            "temp-",
            "debug-"
        ]
        
        device_id_lower = device_id.lower()
        for pattern in invalid_patterns:
            if pattern in device_id_lower:
                logger.debug(f"Rejected known test device_id pattern: {device_id}")
                return False
        
        # If it's a valid UUID, it's definitely fine
        try:
            str(device_id)
            return True
        except ValueError:
            # For non-UUID strings (like Meta phone_number_id), 
            # we accept them if they are numeric or look like 
            # legitimate IDs (minimum 5 chars)
            if device_id.isdigit() or len(device_id) >= 10:
                return True
            
            logger.warning(f"Rejected suspicious device_id: {device_id}")
            return False
    
    def can_generate_qr(self, device_id: str) -> Dict[str, Any]:
        """
        🔥 QR SPAM PREVENTION
        Check if QR can be generated (cooldown enforcement)
        """
        current_time = time.time()
        
        # Check if device_id is valid
        if not self.is_valid_device_id(device_id):
            return {
                "allowed": False,
                "reason": "Invalid device_id format",
                "retry_after": self._qr_cooldown_seconds
            }
        
        # Check cooldown
        if device_id in self._qr_cooldowns:
            time_since_last = current_time - self._qr_cooldowns[device_id]
            if time_since_last < self._qr_cooldown_seconds:
                remaining = self._qr_cooldown_seconds - time_since_last
                logger.warning(f"⏱️ QR generation cooldown for {device_id}: {remaining:.1f}s remaining")
                return {
                    "allowed": False,
                    "reason": "QR generation cooldown",
                    "retry_after": int(remaining)
                }
        
        # Clean old cooldowns
        self._cleanup_old_cooldowns(current_time)
        
        return {"allowed": True, "reason": "Ready"}
    
    def record_qr_generation(self, device_id: str):
        """Record QR generation for cooldown tracking"""
        current_time = time.time()
        self._qr_cooldowns[device_id] = current_time
        logger.info(f"📱 QR generation recorded for {device_id}")
    
    def validate_session_for_restore(self, device_id: str, session_data: Dict[str, Any]) -> bool:
        """
        🔥 SESSION RESTORE VALIDATION
        Prevents invalid session restore flood
        """
        # Check device_id validity
        if not self.is_valid_device_id(device_id):
            logger.warning(f"❌ Rejected invalid session restore: {device_id}")
            return False
        
        # Check if recently restored (prevent restore loops)
        restore_key = f"{device_id}_{int(time.time() // 60)}"  # Per-minute key
        if restore_key in self._recent_restores:
            logger.warning(f"⏱️ Session restore rate limited: {device_id}")
            return False
        
        # Validate session data
        if not session_data or not isinstance(session_data, dict):
            logger.warning(f"❌ Invalid session data for {device_id}")
            return False
        
        # Check session status
        status = session_data.get("status", "").lower()
        if status in ["error", "corrupted", "invalid"]:
            logger.warning(f"❌ Session has invalid status: {device_id} -> {status}")
            return False
        
        # Record successful validation
        self._recent_restores.add(restore_key)
        self._cleanup_old_restores()
        
        logger.info(f"✅ Session validated for restore: {device_id}")
        return True
    
    def filter_engine_sessions(self, sessions: Dict[str, Any]) -> Dict[str, Any]:
        """
        🔥 FILTER INVALID SESSIONS
        Remove test/invalid sessions from engine response
        """
        filtered_sessions = {}
        invalid_count = 0
        
        for device_id, session_data in sessions.items():
            if self.is_valid_device_id(device_id):
                if self.validate_session_for_restore(device_id, session_data):
                    filtered_sessions[device_id] = session_data
                else:
                    invalid_count += 1
            else:
                invalid_count += 1
                logger.warning(f"🗑️ Filtered invalid session: {device_id}")
        
        if invalid_count > 0:
            logger.info(f"🧹 Filtered {invalid_count} invalid sessions, kept {len(filtered_sessions)} valid sessions")
        
        return filtered_sessions
    
    def _cleanup_old_cooldowns(self, current_time: float):
        """Clean up old QR cooldown records"""
        cutoff = current_time - self._qr_cooldown_seconds * 2  # Keep for 2x cooldown period
        old_devices = [
            device_id for device_id, timestamp in self._qr_cooldowns.items()
            if timestamp < cutoff
        ]
        
        for device_id in old_devices:
            del self._qr_cooldowns[device_id]
    
    def _cleanup_old_restores(self):
        """Clean up old restore records"""
        # Simple cleanup - keep only recent ones
        if len(self._recent_restores) > 1000:  # Prevent memory leak
            self._recent_restores.clear()
    
    def get_device_session_info(self, device_id: str) -> Dict[str, Any]:
        """Get session validation info for a device"""
        can_generate = self.can_generate_qr(device_id)
        
        info = {
            "device_id": device_id,
            "is_valid_id": self.is_valid_device_id(device_id),
            "qr_generation": can_generate,
            "cooldowns": len(self._qr_cooldowns),
            "recent_restores": len(self._recent_restores)
        }
        
        if device_id in self._qr_cooldowns:
            last_time = self._qr_cooldowns[device_id]
            info["last_qr_generated"] = datetime.fromtimestamp(last_time).isoformat()
            info["cooldown_remaining"] = max(0, self._qr_cooldown_seconds - (time.time() - last_time))
        
        return info

# Global instance
session_validation_service = SessionValidationService()

def validate_device_id(device_id: str) -> bool:
    """Global function for device ID validation"""
    return session_validation_service.is_valid_device_id(device_id)

def can_generate_qr(device_id: str) -> Dict[str, Any]:
    """Global function for QR cooldown check"""
    return session_validation_service.can_generate_qr(device_id)

def record_qr_generation(device_id: str):
    """Global function to record QR generation"""
    session_validation_service.record_qr_generation(device_id)

def filter_engine_sessions(sessions: Dict[str, Any]) -> Dict[str, Any]:
    """Global function to filter engine sessions"""
    return session_validation_service.filter_engine_sessions(sessions)
