import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from db.session import get_db
from models.busi_user import BusiUser
from models.device import Device, DeviceType
from api.auth_ws import get_current_user_ws
from services.websocket_manager import websocket_manager

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/ws",
    tags=["WebSocket"]
)

@router.websocket("/replies/{device_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    device_id: str,
    token: str = Query(..., description="Authentication token")
):
    """
    WebSocket endpoint for real-time message updates.
    Provides live updates for new messages, read status, and connection changes.
    """
    try:
        # Authenticate user via token
        from db.session import SessionLocal
        db = SessionLocal()
        
        try:
            # Get user from token
            user = await get_current_user_ws(token, db)
            if not user:
                await websocket.close(code=4001, reason="Authentication failed")
                return
            
            # Verify device access
            from services.uuid_service import UUIDService
            device_uuid = UUIDService.safe_convert(device_id)
            device = db.query(Device).filter(
                Device.device_id == device_uuid,
                Device.busi_user_id == user.busi_user_id,
                Device.device_type == DeviceType.web
            ).first()
            
            if not device:
                await websocket.close(code=4003, reason="Device not found or not accessible")
                return
            
            # Connect WebSocket
            await websocket_manager.connect(websocket, str(user.busi_user_id))
            
            # Send initial connection confirmation
            await websocket.send_text(json.dumps({
                "type": "connection_established",
                "device_id": device_id,
                "device_name": device.device_name,
                "status": device.session_status.value if hasattr(device.session_status, "value") else str(device.session_status),
                "message": "WebSocket connection established successfully"
            }))
            
            # Keep connection alive and handle incoming messages
            try:
                while True:
                    # Receive message from client
                    data = await websocket.receive_text()
                    message_data = json.loads(data)
                    
                    # Handle client messages (e.g., mark as read, typing indicators)
                    await handle_client_message(message_data, device_id, user, db, websocket)
                    
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for user {user.busi_user_id}, device {device_id}")
            
        finally:
            db.close()
            
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected during handshake")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close(code=4000, reason="Internal server error")

async def handle_client_message(
    message_data: dict, 
    device_id: str, 
    user: BusiUser, 
    db: Session, 
    websocket: WebSocket
):
    """Handle incoming messages from WebSocket client"""
    
    message_type = message_data.get("type")
    
    try:
        if message_type == "mark_read":
            # Handle mark as read request
            phone = message_data.get("phone")
            if phone:
                from models.whatsapp_messages import WhatsAppMessages
                from services.uuid_service import UUIDService
                
                device_uuid = UUIDService.safe_convert(device_id)
                
                # Update unread messages as read
                updated_count = db.query(WhatsAppMessages).filter(
                    WhatsAppMessages.device_id == device_uuid,
                    WhatsAppMessages.phone == phone,
                    WhatsAppMessages.from_me == False,
                    WhatsAppMessages.is_read == False
                ).update({"is_read": True}, synchronize_session=False)
                
                if updated_count > 0:
                    db.commit()
                    
                    # Broadcast read notification to other connections
                    await websocket_manager.broadcast_message_read(phone, device_id, db)
                    
                    # Send confirmation
                    await websocket.send_text(json.dumps({
                        "type": "messages_marked_read",
                        "phone": phone,
                        "updated_count": updated_count
                    }))
        
        elif message_type == "ping":
            # Handle ping for connection health check
            await websocket.send_text(json.dumps({
                "type": "pong",
                "timestamp": "now"
            }))
        
        elif message_type == "typing":
            # Handle typing indicators (can be extended)
            await websocket.send_text(json.dumps({
                "type": "typing_received",
                "phone": message_data.get("phone"),
                "is_typing": message_data.get("is_typing", False)
            }))
        
        else:
            logger.warning(f"Unknown WebSocket message type: {message_type}")
            
    except Exception as e:
        logger.error(f"Error handling client message: {e}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": "Failed to process message"
        }))

@router.get("/status")
async def websocket_status(
    current_user: BusiUser = Depends(get_current_user_ws)
):
    """Get WebSocket connection status"""
    try:
        connection_count = websocket_manager.get_connection_count(str(current_user.busi_user_id))
        total_connections = websocket_manager.get_total_connections()
        
        return {
            "status": "active",
            "user_connections": connection_count,
            "total_connections": total_connections,
            "message": "WebSocket server is running"
        }
        
    except Exception as e:
        logger.error(f"Error getting WebSocket status: {e}")
        return {
            "status": "error",
            "message": "Failed to get WebSocket status"
        }
