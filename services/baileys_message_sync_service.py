import asyncio
import logging
import json
import aiohttp
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from models.device import Device
from models.whatsapp_messages import WhatsAppMessages
from services.uuid_service import UUIDService
from services.websocket_manager import websocket_manager
from core.config import settings
from utils.phone_utils import normalize_phone

logger = logging.getLogger(__name__)

class BaileysMessageSyncService:
    """
    Production-ready Baileys WhatsApp Web API message synchronization service.
    Handles real-time message synchronization with proper event handling.
    """
    
    def __init__(self, db: Session = None):
        self.db = db
        self.engine_url = settings.WHATSAPP_ENGINE_BASE_URL
        self.synced_devices = set()  # Track devices that have completed initial sync
        self.active_connections = {}  # Track active WebSocket connections per device
        
    async def start_device_sync(self, device_id: str) -> Dict[str, Any]:
        """
        Start message synchronization for a device after QR scan/connection.
        Handles initial sync and sets up real-time event listeners.
        """
        logger.info(f"Starting message sync for device {device_id}")
        
        try:
            # Step 1: Verify device is connected
            device_status = await self._check_device_status(device_id)
            if device_status.get("status") != "connected":
                return {
                    "success": False,
                    "error": f"Device not connected. Status: {device_status.get('status')}"
                }
            
            # Step 2: Perform initial message sync
            initial_sync_result = await self._perform_initial_sync(device_id)
            if not initial_sync_result["success"]:
                return initial_sync_result
            
            # Step 3: Set up real-time event listeners
            await self._setup_event_listeners(device_id)
            
            # Step 4: Mark device as synced
            self.synced_devices.add(device_id)
            
            logger.info(f"Message sync started successfully for device {device_id}")
            return {
                "success": True,
                "messages_synced": initial_sync_result.get("messages_count", 0),
                "chats_synced": initial_sync_result.get("chats_count", 0)
            }
            
        except Exception as e:
            logger.error(f"Failed to start message sync for device {device_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def _perform_initial_sync(self, device_id: str) -> Dict[str, Any]:
        """
        Perform initial synchronization of chats and messages.
        Fetches historical data using Baileys events.
        """
        logger.info(f"Performing initial sync for device {device_id}")
        
        try:
            # Fetch all chats first
            chats_result = await self._fetch_chats(device_id)
            if not chats_result["success"]:
                return chats_result
            
            chats = chats_result.get("chats", [])
            logger.info(f"Fetched {len(chats)} chats for device {device_id}")
            
            # Fetch messages for each chat (focus on individual chats)
            total_messages = 0
            for chat in chats:
                if chat.get("chatType") == "individual":
                    messages_result = await self._fetch_chat_messages(device_id, chat.get("id"))
                    if messages_result["success"]:
                        messages = messages_result.get("messages", [])
                        total_messages += len(messages)
                        
                        # Store messages in database
                        # Note: This method is only called during initial sync which requires a db session
                        if self.db is None:
                            logger.warning("_perform_initial_sync called without db session, skipping message storage")
                        else:
                            await self._store_messages_batch(device_id, messages, self.db)
            
            logger.info(f"Initial sync completed for device {device_id}: {total_messages} messages")
            return {
                "success": True,
                "messages_count": total_messages,
                "chats_count": len(chats)
            }
            
        except Exception as e:
            logger.error(f"Initial sync failed for device {device_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def _fetch_chats(self, device_id: str) -> Dict[str, Any]:
        """Fetch all chats using Baileys chats.set event"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.engine_url}/session/{device_id}/chats",
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        chats_data = await response.json()
                        return {"success": True, "chats": chats_data.get("chats", [])}
                    else:
                        logger.error(f"Failed to fetch chats: HTTP {response.status}")
                        return {"success": False, "error": f"HTTP {response.status}"}
                
        except Exception as e:
            logger.error(f"Error fetching chats for device {device_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def _fetch_chat_messages(self, device_id: str, chat_jid: str, limit: int = 100) -> Dict[str, Any]:
        """Fetch messages for a specific chat using Baileys messages.set event"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.engine_url}/session/{device_id}/messages/{chat_jid}?limit={limit}",
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        messages_data = await response.json()
                        return {"success": True, "messages": messages_data.get("messages", [])}
                    else:
                        logger.error(f"Failed to fetch messages for {chat_jid}: HTTP {response.status}")
                        return {"success": False, "error": f"HTTP {response.status}"}
                
        except Exception as e:
            logger.error(f"Error fetching messages for {chat_jid}: {e}")
            return {"success": False, "error": str(e)}
    
    async def _store_messages_batch(self, device_id: str, messages: List[Dict[str, Any]], db: Session) -> int:
        """Store a batch of messages in the database with deduplication"""
        stored_count = 0
        
        try:
            device_uuid = UUIDService.safe_convert(device_id)
            
            for msg_data in messages:
                # Extract message data
                message_id = msg_data.get("key", {}).get("id")
                if not message_id:
                    continue
                
                # Check if message already exists
                existing = db.query(WhatsAppMessages).filter(
                    WhatsAppMessages.message_id == message_id
                ).first()
                
                if existing:
                    continue  # Skip duplicates
                
                # Extract phone number
                remote_jid = msg_data.get("key", {}).get("remoteJid", "")
                phone = self._extract_phone_from_jid(remote_jid)
                if not phone:
                    continue
                
                # Create message record
                message = WhatsAppMessages(
                    device_id=device_uuid,
                    message_id=message_id,
                    remote_jid=remote_jid,
                    phone=phone,
                    contact_name=msg_data.get("pushName"),
                    message=msg_data.get("message", "") or msg_data.get("conversation", ""),
                    message_type=self._get_message_type(msg_data),
                    timestamp=self._parse_timestamp(msg_data.get("messageTimestamp")),
                    from_me=msg_data.get("key", {}).get("fromMe", False),
                    is_read=msg_data.get("key", {}).get("fromMe", False),  # Outgoing messages are read by default
                    chat_type="individual" if not remote_jid.endswith("@g.us") else "group"
                )
                
                db.add(message)
                stored_count += 1
            
            db.commit()
            logger.info(f"Stored {stored_count} new messages for device {device_id}")
            
        except Exception as e:
            logger.error(f"Error storing message batch: {e}")
            db.rollback()
        
        return stored_count
    
    async def _setup_event_listeners(self, device_id: str):
        """Set up real-time event listeners for new messages"""
        logger.info(f"Setting up event listeners for device {device_id}")
        
        try:
            # Register webhook for real-time events
            webhook_url = f"{settings.API_BASE_URL}/api/webhooks/whatsapp/{device_id}"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.engine_url}/session/{device_id}/webhook",
                    json={
                        "webhook_url": webhook_url,
                        "events": ["messages.upsert", "chats.set", "messages.set"]
                    },
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info(f"Event listeners configured for device {device_id}")
                    else:
                        logger.error(f"Failed to setup event listeners: HTTP {response.status}")
                
        except Exception as e:
            logger.error(f"Error setting up event listeners: {e}")
    
    async def handle_message_upsert(self, device_id: str, event_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """
        Handle real-time message upsert events from Baileys.
        This is called by the webhook endpoint.
        """
        try:
            messages = event_data.get("messages", [])
            stored_count = 0
            
            for msg_data in messages:
                # Extract and validate message data
                message_id = msg_data.get("key", {}).get("id")
                if not message_id:
                    continue
                
                # Check for duplicates
                existing = db.query(WhatsAppMessages).filter(
                    WhatsAppMessages.message_id == message_id
                ).first()
                
                if existing:
                    continue
                
                # Extract phone and other data
                remote_jid = msg_data.get("key", {}).get("remoteJid", "")
                phone = self._extract_phone_from_jid(remote_jid)
                if not phone:
                    continue
                
                # Store new message
                device_uuid = UUIDService.safe_convert(device_id)
                message = WhatsAppMessages(
                    device_id=device_uuid,
                    message_id=message_id,
                    remote_jid=remote_jid,
                    phone=phone,
                    contact_name=msg_data.get("pushName"),
                    message=msg_data.get("message", "") or msg_data.get("conversation", ""),
                    message_type=self._get_message_type(msg_data),
                    timestamp=self._parse_timestamp(msg_data.get("messageTimestamp")),
                    from_me=msg_data.get("key", {}).get("fromMe", False),
                    is_read=msg_data.get("key", {}).get("fromMe", False),
                    chat_type="individual" if not remote_jid.endswith("@g.us") else "group"
                )
                
                db.add(message)
                stored_count += 1
            
            db.commit()
            logger.info(f"Stored {stored_count} new messages from real-time event for device {device_id}")
            
            # Broadcast new messages via WebSocket
            if stored_count > 0:
                for msg_data in messages:
                    if msg_data.get("key", {}).get("id") in [m.message_id for m in db.query(WhatsAppMessages).filter(WhatsAppMessages.message_id.in_([msg_data.get("key", {}).get("id") for msg_data in messages])).all()]:
                        await websocket_manager.broadcast_new_message(msg_data, device_id, db)
            
            return {
                "success": True,
                "stored_count": stored_count
            }
            
        except Exception as e:
            logger.error(f"Error handling message upsert for device {device_id}: {e}")
            db.rollback()
            return {"success": False, "error": str(e)}
    
    async def handle_chats_set(self, device_id: str, event_data: Dict[str, Any]):
        """Handle chats.set events for chat updates"""
        logger.info(f"Handling chats.set event for device {device_id}")
        # Can be implemented for chat metadata updates if needed
    
    async def handle_messages_set(self, device_id: str, event_data: Dict[str, Any], db: Session):
        """Handle messages.set events for message history updates"""
        logger.info(f"Handling messages.set event for device {device_id}")
        messages = event_data.get("messages", [])
        if messages:
            await self._store_messages_batch(device_id, messages, db)
    
    def _extract_phone_from_jid(self, remote_jid: str) -> Optional[str]:
        """Extract clean phone number from WhatsApp JID"""
        if not remote_jid:
            return None
        
        # Remove domain suffix
        phone = remote_jid.split("@")[0]
        
        # Normalize phone number
        return normalize_phone(phone)
    
    def _get_message_type(self, msg_data: Dict[str, Any]) -> str:
        """Determine message type from Baileys message data"""
        message = msg_data.get("message", {})
        
        if message.get("conversation"):
            return "text"
        elif message.get("imageMessage"):
            return "image"
        elif message.get("documentMessage"):
            return "document"
        elif message.get("videoMessage"):
            return "video"
        elif message.get("audioMessage"):
            return "audio"
        elif message.get("stickerMessage"):
            return "sticker"
        else:
            return "unknown"
    
    def _parse_timestamp(self, timestamp: Any) -> datetime:
        """Parse timestamp from Baileys event data"""
        if isinstance(timestamp, (int, float)):
            return datetime.fromtimestamp(timestamp, tz=timezone.utc)
        elif isinstance(timestamp, str):
            try:
                return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except:
                return datetime.now(timezone.utc)
        else:
            return datetime.now(timezone.utc)
    
    async def _check_device_status(self, device_id: str) -> Dict[str, Any]:
        """Check device connection status"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.engine_url}/session/{device_id}/status",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {"success": True, "status": data.get("status")}
                    else:
                        return {"success": False, "error": f"HTTP {response.status}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_device_conversations(self, device_id: str, limit: int = 50, db: Session = None) -> List[Dict[str, Any]]:
        """
        Get conversation summary for a device.
        Returns grouped conversations with last message and unread counts.
        """
        if db is None:
            logger.warning("get_device_conversations called without db session")
            return []
            
        try:
            device_uuid = UUIDService.safe_convert(device_id)
            
            # SQL query for conversation summary
            query = db.execute("""
                SELECT 
                    phone,
                    MAX(contact_name) as contact_name,
                    MAX(message) as last_message,
                    MAX(timestamp) as last_message_time,
                    COUNT(*) FILTER (WHERE is_read = false AND from_me = false) as unread_count,
                    COUNT(*) as total_messages
                FROM whatsapp_messages 
                WHERE device_id = :device_id 
                    AND chat_type = 'individual'
                GROUP BY phone
                ORDER BY MAX(timestamp) DESC
                LIMIT :limit
            """, {"device_id": device_uuid, "limit": limit})
            
            results = []
            for row in query:
                results.append({
                    "phone": row.phone,
                    "contact_name": row.contact_name or row.phone,
                    "last_message": row.last_message,
                    "last_message_time": row.last_message_time,
                    "unread_count": row.unread_count or 0,
                    "total_messages": row.total_messages
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting conversations for device {device_id}: {e}")
            return []

# Global instance
baileys_sync_service = BaileysMessageSyncService()
