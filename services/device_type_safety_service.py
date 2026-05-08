"""
🔥 DEVICE TYPE SAFETY SERVICE
Enforces strict separation between OFFICIAL and UNOFFICIAL devices
Prevents mixing of device types in workflows
"""
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from models.device import Device, DeviceType, SessionStatus

logger = logging.getLogger(__name__)

class DeviceTypeSafetyService:
    """
    🔥 CRITICAL SAFETY SERVICE
    Enforces strict device type separation rules:
    - Official devices: Only for Official WhatsApp Cloud API
    - Unofficial devices: Only for QR/Web/Baileys workflows
    - NEVER mix device types in any workflow
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def validate_device_type_for_workflow(self, device_id: str, workflow_type: str) -> Dict[str, Any]:
        """
        Validate that a device is allowed for the specific workflow type
        
        workflow_type options:
        - 'official_messaging': Official WhatsApp Cloud API messaging
        - 'qr_generation': QR code generation (unofficial only)
        - 'manage_replies': Manage Replies UI (unofficial only)
        - 'webhook_incoming': Incoming webhook (unofficial only)
        - 'google_sheets': Google Sheets automation (official only)
        """
        try:
            device = self.db.query(Device).filter(Device.device_id == device_id).first()
            if not device:
                return {"valid": False, "error": "Device not found"}
            
            # 🔥 STRICT WORKFLOW VALIDATION
            official_workflows = ['official_messaging', 'google_sheets']
            unofficial_workflows = ['qr_generation', 'manage_replies', 'webhook_incoming']
            
            if workflow_type in official_workflows:
                if device.device_type != DeviceType.official:
                    return {
                        "valid": False,
                        "error": f"Device {device_id} is type {device.device_type} but workflow '{workflow_type}' requires OFFICIAL device",
                        "device_type": str(device.device_type),
                        "required_type": "OFFICIAL"
                    }
            
            elif workflow_type in unofficial_workflows:
                if device.device_type != DeviceType.web:
                    return {
                        "valid": False,
                        "error": f"Device {device_id} is type {device.device_type} but workflow '{workflow_type}' requires web device",
                        "device_type": str(device.device_type),
                        "required_type": "UNOFFICIAL"
                    }
            else:
                return {"valid": False, "error": f"Unknown workflow type: {workflow_type}"}
            
            # Additional validation: device must be connected for most workflows
            if workflow_type != 'qr_generation' and device.session_status != SessionStatus.connected:
                return {
                    "valid": False,
                    "error": f"Device {device_id} is not connected (status: {device.session_status})",
                    "device_status": str(device.session_status)
                }
            
            return {"valid": True, "device": device}
            
        except Exception as e:
            logger.error(f"Error validating device type for workflow {workflow_type}: {e}")
            return {"valid": False, "error": f"Validation error: {str(e)}"}
    
    def get_official_devices(self, user_id: str, connected_only: bool = True) -> List[Device]:
        """Get OFFICIAL devices for a user"""
        query = self.db.query(Device).filter(
            Device.busi_user_id == user_id,
            Device.device_type == DeviceType.official,
            Device.is_active.is_(True)
        )
        
        if connected_only:
            query = query.filter(Device.session_status == SessionStatus.connected)
        
        return query.all()
    
    def get_unofficial_devices(self, user_id: str, connected_only: bool = True) -> List[Device]:
        """Get web devices for a user"""
        query = self.db.query(Device).filter(
            Device.busi_user_id == user_id,
            Device.device_type == DeviceType.web,
            Device.is_active.is_(True)
        )
        
        if connected_only:
            query = query.filter(Device.session_status == SessionStatus.connected)
        
        return query.all()
    
    def enforce_device_type_isolation(self, user_id: str) -> Dict[str, Any]:
        """
        Check for any device type mixing issues in user's devices
        Returns safety report
        """
        try:
            official_devices = self.get_official_devices(user_id, connected_only=False)
            unofficial_devices = self.get_unofficial_devices(user_id, connected_only=False)
            
            # Check for potential issues
            issues = []
            
            # Issue 1: Official devices with QR codes (shouldn't happen)
            for device in official_devices:
                if device.qr_last_generated:
                    issues.append({
                        "type": "official_device_with_qr",
                        "device_id": str(device.device_id),
                        "device_name": device.device_name,
                        "description": "Official device has QR code (should not exist)"
                    })
            
            # Issue 2: Unofficial devices in official workflows
            for device in unofficial_devices:
                if "Official WhatsApp" in device.device_name:
                    issues.append({
                        "type": "unofficial_device_with_official_name",
                        "device_id": str(device.device_id),
                        "device_name": device.device_name,
                        "description": "Unofficial device has 'Official' in name (confusing)"
                    })
            
            return {
                "safe": len(issues) == 0,
                "issues": issues,
                "official_count": len(official_devices),
                "unofficial_count": len(unofficial_devices),
                "total_devices": len(official_devices) + len(unofficial_devices)
            }
            
        except Exception as e:
            logger.error(f"Error checking device type isolation: {e}")
            return {
                "safe": False,
                "issues": [{"type": "check_error", "description": f"Error during safety check: {str(e)}"}],
                "official_count": 0,
                "unofficial_count": 0,
                "total_devices": 0
            }
    
    def sanitize_device_list_by_type(self, devices: List[Device], allowed_type: DeviceType) -> List[Device]:
        """
        Filter device list to only include allowed device type
        Used as safety net in APIs
        """
        return [device for device in devices if device.device_type == allowed_type]
    
    def log_device_type_violation(self, device_id: str, workflow_type: str, violation_details: str):
        """Log device type violations for monitoring"""
        logger.warning(f"🚨 DEVICE TYPE SAFETY VIOLATION: Device {device_id} in workflow '{workflow_type}': {violation_details}")
        
        # TODO: Could send to monitoring system, create audit log, etc.

# Global instance for easy access
device_type_safety_service = None

def get_device_type_safety_service(db: Session) -> DeviceTypeSafetyService:
    """Get or create device type safety service instance"""
    global device_type_safety_service
    if device_type_safety_service is None:
        device_type_safety_service = DeviceTypeSafetyService(db)
    return device_type_safety_service

# Convenience functions for common validations
def validate_official_device(db: Session, device_id: str, workflow_type: str = "official_messaging") -> Dict[str, Any]:
    """Validate device is OFFICIAL for official workflows"""
    safety_service = get_device_type_safety_service(db)
    return safety_service.validate_device_type_for_workflow(device_id, workflow_type)

def validate_unofficial_device(db: Session, device_id: str, workflow_type: str = "manage_replies") -> Dict[str, Any]:
    """Validate device is UNOFFICIAL for unofficial workflows"""
    safety_service = get_device_type_safety_service(db)
    return safety_service.validate_device_type_for_workflow(device_id, workflow_type)
