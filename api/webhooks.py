#!/usr/bin/env python3
"""
WhatsApp Incoming Webhooks API
Handles incoming messages from WhatsApp Engine
"""

import logging
import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any

from db.session import get_db
from db.session import SessionLocal
from models.device import Device
from models.whatsapp_inbox import WhatsAppInbox
from services.uuid_service import UUIDService
from utils.phone_utils import normalize_phone
from services.message_backfill_service import backfill_unread_messages_for_device
from services.baileys_message_sync_service import baileys_sync_service
from services.message_sync_initiator import message_sync_initiator

from services.chatbot_service import chatbot_service
from core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/whatsapp/incoming")
async def receive_whatsapp_message(payload: Dict[str, Any], background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    try:
        # logger.info(f"[WEBHOOK] 📩 Processing incoming metadata...")
        msg_id = payload.get("message_id")
        status = payload.get("status")
        
        # 1. ALWAYS ALLOW STATUS UPDATES (Requirements: Read/Sync from phone)
        if msg_id and status:
            existing = db.query(WhatsAppInbox).filter(WhatsAppInbox.message_id == msg_id).first()
            if existing:
                if status in ["read", "viewed"]:
                    existing.is_read = True
                    db.commit()
                    return {"status": "success", "action": "inbox_status_updated"}
        
        # Original logic re-enabled below...
        timestamp = datetime.now(timezone.utc)

        remote_jid = payload.get("remoteJid") or payload.get("jid") or payload.get("remote_jid")

        # STRICT INDIVIDUAL FILTERING:
        # Only allow @s.whatsapp.net (regular) and @lid (new format)
        # Explicitly ignore @g.us (groups), @broadcast (broadcast lists), etc.
        is_individual = remote_jid and ("@s.whatsapp.net" in remote_jid or "@lid" in remote_jid)
        
        if not is_individual:
            logger.info(f"[WEBHOOK] Ignoring non-individual jid: {remote_jid}")
            return {"status": "ignored", "reason": "not_individual_chat"}

        # 1. STATUS UPDATE HANDLING (Requirement: Sync read status from mobile)
        msg_id = payload.get("message_id")
        status = payload.get("status")
        
        if msg_id and status:
            # Check if this is a status update for an existing message
            existing = db.query(WhatsAppInbox).filter(WhatsAppInbox.message_id == msg_id).first()
            if existing:
                if status in ["read", "viewed"]:
                    logger.info(f"[WEBHOOK] ✅ Marking message {msg_id} as READ via status update")
                    existing.is_read = True
                
                # Also handle delivery status if needed
                db.commit()
                return {"status": "success", "action": "status_updated", "message_id": msg_id}

        # 2. DEDUPLICATION CHECK (Crucial for sync)
        if msg_id:
            existing = db.query(WhatsAppInbox).filter(WhatsAppInbox.message_id == msg_id).first()
            if existing:
                logger.debug(f"[WEBHOOK] ⏩ Message {msg_id} already exists, skipping duplicate")
                return {"status": "ignored", "reason": "duplicate_message_id"}

        # Extract phone strictly - handle LID and other JID formats
        phone = None
        is_lid_jid = remote_jid and "@lid" in remote_jid
        
        if remote_jid:
            phone = remote_jid.split("@")[0]
        
        # Fallback only if remote_jid was missing (unlikely if engine is fixed)
        if not phone:
             phone = payload.get("phone") or payload.get("phone_number")

        # Sanitize using phone normalization (this will handle LID extraction)
        if phone:
            phone = normalize_phone(phone)

        # SPECIAL HANDLING: For LID JIDs, try to get the real participant phone
        if is_lid_jid:
            participant = payload.get("participant")
            if participant:
                participant_phone = normalize_phone(participant.split("@")[0])
                if participant_phone:
                    phone = participant_phone
                    logger.info(f"[WEBHOOK] 🔄 Swapped LID JID with participant phone: {phone}")
            
            # If still None or if participant failed, we keep the original 'phone' 
            # (which is the LID number extracted earlier) rather than ignoring it.
            if not phone:
                 logger.warning(f"[WEBHOOK] LID JID without participant fallback: {remote_jid}")
                 # 'phone' remains the LID number from line 49/57

        # STRICT SAFETY CHECK: If phone is longer than 16 digits, it's likely a Message ID or UUID
        if not phone or len(phone) > 16:
            logger.warning(f"[WEBHOOK] ⛔ Ignored invalid/long phone (likely ID): {phone} Raw JID: {remote_jid}")
            return {"status": "ignored", "reason": "invalid_phone_length"}

        from_me = payload.get("from_me", False)

        device_uuid = UUIDService.safe_convert(payload.get("device_id"))
        if not device_uuid:
            return {"status": "ignored"}

        device = db.query(Device).filter(Device.device_id == device_uuid).first()
        if not device:
            return {"status": "ignored"}

        # Always insert a NEW row for every incoming message (or outgoing from phone)
        # This ensures full conversation history is preserved
        # Update contact_name on all rows for this phone if push_name provided
        push_name = payload.get("push_name")
        if push_name:
            db.query(WhatsAppInbox).filter(
                WhatsAppInbox.device_id == device_uuid,
                WhatsAppInbox.phone_number == phone
            ).update({"contact_name": push_name}, synchronize_session=False)

        # Calculate read status:
        # Priority 1: Payload explicitly says is_read (e.g. historical sync)
        # Priority 2: From me = always read
        # Priority 3: Incoming message = unread by default
        is_read_flag = payload.get("is_read")
        if is_read_flag is not None:
             final_is_read = is_read_flag
        else:
             final_is_read = True if from_me else False

        new_msg = WhatsAppInbox(
            device_id=device_uuid,
            phone_number=phone,
            contact_name=push_name or phone,
            chat_type="individual",
            incoming_message=payload.get("message"),
            message_id=msg_id,
            incoming_time=datetime.now(timezone.utc),
            is_read=final_is_read,
            is_replied=True if from_me else False,
            is_outgoing=from_me,
            remote_jid=remote_jid  # Save the full JID for accurate replies later
        )

        db.add(new_msg)
        db.commit()
        db.refresh(new_msg)

        # 🚀 [CHATBOT INTEGRATION]
        # Trigger AI auto-reply if enabled and not from me
        if settings.ENABLE_AI_CHATBOT and not from_me and payload.get("message"):
            logger.info(f"🤖 [CHATBOT] Triggering AI auto-reply for {phone}")
            background_tasks.add_task(
                chatbot_service.process_incoming_message,
                str(device_uuid),
                phone,
                payload.get("message"),
                remote_jid
            )

        return {"status": "success", "action": "created", "message_id": str(new_msg.id)}

    except Exception as e:
        logger.error(f"[WEBHOOK] Error: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/whatsapp/status")
async def receive_whatsapp_status(payload: Dict[str, Any], db: Session = Depends(get_db)):
    """
    🔥 Handle real-time delivery status updates from the engine
    Updates 'Message' model based on messageId
    """
    try:
        msg_id = payload.get("message_id")
        status = payload.get("status") # 'sent', 'delivered', 'read'
        
        if not msg_id or not status:
            return {"status": "ignored", "reason": "missing_data"}

        from models.message import Message
        
        # Mapping Baileys status to our status
        # status 2 = sent, 3 = delivered, 4 = read
        status_map = {
            "2": "sent",
            "sent": "sent",
            "3": "delivered",
            "delivered": "delivered",
            "4": "read",
            "read": "read"
        }
        
        final_status = status_map.get(str(status), status)
        
        # Update the Message table (Delivery Reports)
        message = db.query(Message).filter(Message.message_id == msg_id).first()
        if message:
            # Normalize to uppercase for Enum matching
            message.status = final_status.upper()
            db.commit()
            return {"status": "success", "action": "status_updated", "message_id": msg_id}
            
        return {"status": "not_found", "message_id": msg_id}

    except Exception as e:
        logger.error(f"[STATUS_WEBHOOK] Error: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/whatsapp/{device_id}")
async def whatsapp_baileys_webhook(
    device_id: str,
    payload: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Handle real-time Baileys WhatsApp events.
    Supports: messages.upsert, chats.set, messages.set
    """
    try:
        # Verify device exists and is accessible
        device_uuid = UUIDService.safe_convert(device_id)
        device = db.query(Device).filter(
            Device.device_id == device_uuid
        ).first()
        
        if not device:
            logger.warning(f"[BAILEYS] Webhook received for unknown device: {device_id}")
            return {"status": "ignored", "reason": "device_not_found"}
        
        # Determine event type and handle accordingly
        event_type = payload.get("event")
        
        if event_type == "messages.upsert":
            result = await baileys_sync_service.handle_message_upsert(device_id, payload, db)
            logger.info(f"[BAILEYS] Processed messages.upsert for device {device_id}: {result}")
            return result
            
        elif event_type == "chats.set":
            await baileys_sync_service.handle_chats_set(device_id, payload)
            logger.info(f"[BAILEYS] Processed chats.set for device {device_id}")
            return {"status": "success", "event": "chats.set"}
            
        elif event_type == "messages.set":
            await baileys_sync_service.handle_messages_set(device_id, payload, db)
            logger.info(f"[BAILEYS] Processed messages.set for device {device_id}")
            return {"status": "success", "event": "messages.set"}
            
        else:
            logger.warning(f"[BAILEYS] Unknown event type: {event_type}")
            return {"status": "ignored", "reason": "unknown_event"}
        
    except Exception as e:
        logger.error(f"[BAILEYS] Error processing webhook for device {device_id}: {e}")
        return {"status": "error", "message": str(e)}


@router.get("/whatsapp/{device_id}/test")
async def test_baileys_webhook(
    device_id: str,
    db: Session = Depends(get_db)
):
    """
    Test endpoint to verify Baileys webhook configuration.
    """
    try:
        # Verify device exists
        device_uuid = UUIDService.safe_convert(device_id)
        device = db.query(Device).filter(
            Device.device_id == device_uuid
        ).first()
        
        if not device:
            return {"status": "error", "message": "Device not found"}
        
        return {
            "status": "webhook_ready",
            "device_id": device_id,
            "device_name": device.device_name,
            "message": "Baileys webhook endpoint is ready to receive events"
        }
        
    except Exception as e:
        logger.error(f"[BAILEYS] Error testing webhook: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/connection/update")
async def connection_update(
    payload: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    try:
        device_uuid = UUIDService.safe_convert(payload.get("device_id"))
        if not device_uuid:
            return {"status": "ignored"}

        device = db.query(Device).filter(Device.device_id == device_uuid).first()
        if not device:
            return {"status": "ignored"}

        status = payload.get("status")

        if status in ["open", "connected"]:
            was_connected = str(device.session_status).lower() in ["connected", "sessionstatus.connected"]
            device.session_status = "connected"
            device.qr_code = None
            device.disconnected_at = None
            db.commit()

            # Best-effort: backfill unread/history from engine ONCE when transitioning to connected.
            # Also start new Baileys message synchronization
            if not was_connected:
                async def _run_backfill_and_sync(dev_id: str):
                    _db = SessionLocal()
                    try:
                        # Legacy backfill for existing system
                        result = backfill_unread_messages_for_device(_db, dev_id, limit=500)
                        if not result.get("success"):
                            logger.warning(f"[BACKFILL] skipped/failed for device={dev_id}: {result}")
                        else:
                            logger.info(f"[BACKFILL] completed for device={dev_id}: {result}")
                        
                        # Start new Baileys message synchronization - use await instead of asyncio.run()
                        await message_sync_initiator.start_sync_on_connection(dev_id, _db)
                        
                    except Exception as e:
                        logger.error(f"[BACKFILL/SYNC] error for device={dev_id}: {e}")
                    finally:
                        _db.close()

                background_tasks.add_task(_run_backfill_and_sync, str(device.device_id))

            return {"status": "success", "event": "connected"}

        if status in ["close", "disconnected"]:
            device.session_status = "disconnected"
            device.disconnected_at = datetime.now(timezone.utc)
            db.commit()
            return {"status": "success", "event": "disconnected"}

        return {"status": "ignored"}

    except Exception as e:
        logger.error(f"[WEBHOOK] Connection update error: {e}")
        return {"status": "error", "message": str(e)}
