import json
import logging
from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class WebSocketManager:
    """
    Production-ready WebSocket manager for real-time WhatsApp message updates.
    Handles multiple device connections and user isolation.
    """
    
    def __init__(self):
        # Store active connections by user_id
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # Store device-specific connections for targeted updates
        self.device_connections: Dict[str, Set[str]] = {}  # device_id -> set of user_ids
        
    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept WebSocket connection and register user"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        
        self.active_connections[user_id].append(websocket)
        logger.info(f"WebSocket connected for user {user_id}. Total connections: {len(self.active_connections[user_id])}")
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        """Remove WebSocket connection and cleanup"""
        if user_id in self.active_connections:
            try:
                self.active_connections[user_id].remove(websocket)
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
                
                # Clean up device connections
                devices_to_remove = []
                for device_id, users in self.device_connections.items():
                    if user_id in users:
                        users.discard(user_id)
                        if not users:
                            devices_to_remove.append(device_id)
                
                for device_id in devices_to_remove:
                    del self.device_connections[device_id]
                
                logger.info(f"WebSocket disconnected for user {user_id}")
                
            except ValueError:
                logger.warning(f"WebSocket not found in active connections for user {user_id}")
    
    async def send_personal_message(self, message: dict, user_id: str):
        """Send message to specific user's all connections"""
        if user_id in self.active_connections:
            disconnected_websockets = []
            
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Error sending WebSocket message to user {user_id}: {e}")
                    disconnected_websockets.append(connection)
            
            # Remove disconnected websockets
            for ws in disconnected_websockets:
                self.disconnect(ws, user_id)
    
    async def broadcast_to_device(self, message: dict, device_id: str, db: Session):
        """Broadcast message to all users who have access to the device"""
        from models.device import Device
        
        # Get all users who have access to this device
        device = db.query(Device).filter(Device.device_id == device_id).first()
        if not device:
            logger.warning(f"Device {device_id} not found for WebSocket broadcast")
            return
        
        user_ids = [str(device.busi_user_id)]
        
        # Send to all connected users for this device
        for user_id in user_ids:
            await self.send_personal_message(message, user_id)
    
    async def broadcast_new_message(self, message_data: dict, device_id: str, db: Session):
        """Broadcast new message notification"""
        notification = {
            "type": "new_message",
            "device_id": device_id,
            "data": message_data,
            "timestamp": message_data.get("timestamp")
        }
        
        await self.broadcast_to_device(notification, device_id, db)
    
    async def broadcast_message_read(self, phone: str, device_id: str, db: Session):
        """Broadcast message read notification"""
        notification = {
            "type": "messages_read",
            "device_id": device_id,
            "phone": phone,
            "timestamp": "now"
        }
        
        await self.broadcast_to_device(notification, device_id, db)
    
    async def broadcast_connection_status(self, device_id: str, status: str, db: Session):
        """Broadcast device connection status change"""
        from models.device import Device
        
        device = db.query(Device).filter(Device.device_id == device_id).first()
        if not device:
            return
        
        notification = {
            "type": "connection_status",
            "device_id": device_id,
            "status": status,
            "device_name": device.device_name,
            "timestamp": "now"
        }
        
        await self.send_personal_message(notification, str(device.busi_user_id))
    
    def get_connection_count(self, user_id: str) -> int:
        """Get number of active connections for a user"""
        return len(self.active_connections.get(user_id, []))
    
    def get_total_connections(self) -> int:
        """Get total number of active connections"""
        return sum(len(connections) for connections in self.active_connections.values())

# Global WebSocket manager instance
websocket_manager = WebSocketManager()
