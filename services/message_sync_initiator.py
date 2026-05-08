import logging
from typing import Dict, Any
from sqlalchemy.orm import Session
from models.device import Device
from services.baileys_message_sync_service import baileys_sync_service
from services.websocket_manager import websocket_manager

logger = logging.getLogger(__name__)

class MessageSyncInitiator:
    """
    Service to initiate message synchronization when devices connect.
    Handles the transition from legacy to new message system.
    """
    
    def __init__(self):
        self.syncing_devices = set()  # Track devices currently syncing
    
    async def start_sync_on_connection(self, device_id: str, db: Session) -> Dict[str, Any]:
        """
        Start message synchronization when a device connects.
        Called by webhook connection update handler.
        """
        try:
            if device_id in self.syncing_devices:
                logger.info(f"Message sync already in progress for device {device_id}")
                return {"success": True, "status": "already_syncing"}
            
            # Verify device exists and is connected
            device = db.query(Device).filter(Device.device_id == device_id).first()
            if not device:
                return {"success": False, "error": "Device not found"}
            
            if str(device.session_status) != "connected":
                return {"success": False, "error": f"Device not connected. Status: {device.session_status}"}
            
            # Mark device as syncing
            self.syncing_devices.add(device_id)
            
            try:
                # Start Baileys message synchronization
                sync_result = await baileys_sync_service.start_device_sync(device_id)
                
                if sync_result["success"]:
                    logger.info(f"Message sync started successfully for device {device_id}")
                    
                    # Broadcast connection status via WebSocket
                    await websocket_manager.broadcast_connection_status(
                        device_id, 
                        "sync_started", 
                        db
                    )
                    
                    return {
                        "success": True,
                        "status": "sync_started",
                        "messages_synced": sync_result.get("messages_synced", 0),
                        "chats_synced": sync_result.get("chats_synced", 0)
                    }
                else:
                    logger.error(f"Failed to start message sync for device {device_id}: {sync_result.get('error')}")
                    return sync_result
                    
            finally:
                # Remove from syncing set regardless of outcome
                self.syncing_devices.discard(device_id)
                
        except Exception as e:
            logger.error(f"Error starting message sync for device {device_id}: {e}")
            self.syncing_devices.discard(device_id)
            return {"success": False, "error": str(e)}
    
    def is_device_syncing(self, device_id: str) -> bool:
        """Check if a device is currently syncing messages"""
        return device_id in self.syncing_devices
    
    def get_syncing_devices(self) -> list:
        """Get list of currently syncing devices"""
        return list(self.syncing_devices)

# Global instance
message_sync_initiator = MessageSyncInitiator()
