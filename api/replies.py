from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from db.session import get_db
from models.whatsapp_inbox import WhatsAppInbox
from models.whatsapp_messages import WhatsAppMessages
from models.device import Device
from models.busi_user import BusiUser
from api.auth import get_current_user
from schemas.whatsapp_inbox import ReplyRequest, InboxMessageResponse, InboxResponse
from services.unified_whatsapp_sender import send_whatsapp_message
from utils.phone_utils import normalize_phone


router = APIRouter(
    tags=["Replies"]
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------
# FETCH INBOX
# ---------------------------------------------------
@router.get("/chat-summary")
async def get_chat_summary(
    current_user: BusiUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Enhanced chat summary with unified message sources.
    Combines legacy WhatsAppInbox and new WhatsAppMessages tables.
    Shows ONLY CONNECTED device chats to match active devices behavior.
    """
    try:
        from models.device import DeviceType
        from sqlalchemy import func, and_, union_all

        # Get ONLY CONNECTED user's web devices
        devices = db.query(Device).filter(
            Device.busi_user_id == current_user.busi_user_id,
            Device.device_type == DeviceType.web,
            Device.session_status == "connected"  # Only connected devices
        ).all()
        device_ids = [d.device_id for d in devices]

        if not device_ids:
            return {"success": True, "data": []}

        # Query from legacy table (WhatsAppInbox)
        legacy_summary = db.query(
            WhatsAppInbox.phone_number,
            WhatsAppInbox.contact_name,
            func.max(WhatsAppInbox.incoming_time).label('last_message_time'),
            func.max(WhatsAppInbox.incoming_message).label('last_message'),
            func.sum(
                func.case(
                    (and_(WhatsAppInbox.is_read == False, WhatsAppInbox.is_outgoing == False), 1),
                    else_=0
                )
            ).label('unread_count'),
            func.count(WhatsAppInbox.id).label('total_messages'),
            func.literal('legacy').label('source')
        ).filter(
            WhatsAppInbox.device_id.in_(device_ids),
            WhatsAppInbox.chat_type == "individual"
        ).group_by(
            WhatsAppInbox.phone_number,
            WhatsAppInbox.contact_name
        )

        # Query from new table (WhatsAppMessages)
        new_summary = db.query(
            WhatsAppMessages.phone,
            WhatsAppMessages.contact_name,
            func.max(WhatsAppMessages.timestamp).label('last_message_time'),
            func.max(WhatsAppMessages.message).label('last_message'),
            func.sum(
                func.case(
                    (and_(WhatsAppMessages.is_read == False, WhatsAppMessages.from_me == False), 1),
                    else_=0
                )
            ).label('unread_count'),
            func.count(WhatsAppMessages.id).label('total_messages'),
            func.literal('new').label('source')
        ).filter(
            WhatsAppMessages.device_id.in_(device_ids),
            WhatsAppMessages.chat_type == "individual"
        ).group_by(
            WhatsAppMessages.phone,
            WhatsAppMessages.contact_name
        )

        # Combine results using union and get the latest message per phone
        combined_query = legacy_summary.union_all(new_summary).subquery()
        
        # Final aggregation to get the latest message per phone number
        final_summary = db.query(
            combined_query.c.phone_number,
            combined_query.c.contact_name,
            func.max(combined_query.c.last_message_time).label('last_message_time'),
            func.max(combined_query.c.last_message).label('last_message'),
            func.sum(combined_query.c.unread_count).label('unread_count'),
            func.sum(combined_query.c.total_messages).label('total_messages')
        ).group_by(
            combined_query.c.phone_number,
            combined_query.c.contact_name
        ).order_by(
            func.max(combined_query.c.last_message_time).desc()
        ).all()

        logger.info(f"[REPLIES] Enhanced chat summary found={len(final_summary)} conversations from connected devices")

        return {
            "success": True,
            "data": [
                {
                    "phone_number": summary.phone_number,
                    "contact_name": summary.contact_name or summary.phone_number,
                    "last_message_time": summary.last_message_time,
                    "last_message": summary.last_message,
                    "unread_count": summary.unread_count or 0,
                    "total_messages": summary.total_messages
                }
                for summary in final_summary
            ]
        }

    except Exception as e:
        logger.error(f"Error fetching enhanced chat summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/unread-messages")
async def get_unread_messages(
    device_id: Optional[str] = None,
    current_user: BusiUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all unread messages from ALL user devices (connected or disconnected).
    Shows unread messages from mobile WhatsApp and all devices.
    """
    try:
        from models.device import DeviceType
        from sqlalchemy import and_

        # 1. Get user's web devices (ALL - connected OR disconnected)
        if device_id:
            device = db.query(Device).filter(
                Device.device_id == device_id,
                Device.busi_user_id == current_user.busi_user_id,
                Device.device_type == DeviceType.web
            ).first()
            if not device:
                raise HTTPException(status_code=404, detail="Device not found or not accessible")
            device_ids = [device.device_id]
        else:
            # Get ALL user's web devices (not just connected ones)
            devices = db.query(Device).filter(
                Device.busi_user_id == current_user.busi_user_id,
                Device.device_type == DeviceType.web
            ).all()
            device_ids = [d.device_id for d in devices]

        if not device_ids:
            return {"success": True, "data": []}

        # 2. Get ALL unread messages from ALL user devices
        unread_messages = db.query(WhatsAppInbox).filter(
            WhatsAppInbox.device_id.in_(device_ids),
            WhatsAppInbox.chat_type == "individual",  # ONLY individual messages, no groups
            WhatsAppInbox.is_read == False,          # Must be unread
            WhatsAppInbox.is_outgoing == False      # Only incoming messages
        ).order_by(WhatsAppInbox.incoming_time.desc()).all()

        logger.info(f"[REPLIES] Found {len(unread_messages)} unread messages from ALL user devices (individual only)")

        # 3. Format response
        response_data = []
        for msg in unread_messages:
            # Clean phone number
            clean_phone = normalize_phone(msg.phone_number)
            if clean_phone:
                msg.phone_number = clean_phone

            # Add TZ info for browser consistency
            if msg.incoming_time and msg.incoming_time.tzinfo is None:
                msg.incoming_time = msg.incoming_time.replace(tzinfo=timezone.utc)

            try:
                msg_dict = InboxMessageResponse.model_validate(msg)
                msg_dict.is_incoming = True  # Unread messages are always incoming
                msg_dict.unread = True         # Explicitly mark as unread
                response_data.append(msg_dict)
                
                # Log each unread message for debugging
                logger.info(f"[REPLIES] Unread message: {msg.contact_name} ({msg.phone_number}) - {msg.incoming_message[:50]}...")
                
            except Exception as val_err:
                logger.error(f"[REPLIES] Unread message {msg.id} serialization error: {val_err}")
                continue

        return {"success": True, "data": response_data}

    except Exception as e:
        logger.error(f"Error fetching unread messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/unread-count")
async def get_unread_count(
    device_id: Optional[str] = None,
    current_user: BusiUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get total unread count per contact from ALL user devices.
    Shows unread counts from mobile WhatsApp and all devices.
    Perfect for unread badges and notifications.
    """
    try:
        from models.device import DeviceType
        from sqlalchemy import func, and_

        # 1. Get user's web devices (ALL - connected OR disconnected)
        if device_id:
            device = db.query(Device).filter(
                Device.device_id == device_id,
                Device.busi_user_id == current_user.busi_user_id,
                Device.device_type == DeviceType.web
            ).first()
            if not device:
                raise HTTPException(status_code=404, detail="Device not found or not accessible")
            device_ids = [device.device_id]
        else:
            # Get ALL user's web devices (not just connected ones)
            devices = db.query(Device).filter(
                Device.busi_user_id == current_user.busi_user_id,
                Device.device_type == DeviceType.web
            ).all()
            device_ids = [d.device_id for d in devices]

        if not device_ids:
            return {"success": True, "data": [], "total_unread": 0}

        # 2. Get unread count per contact from ALL devices
        unread_counts = db.query(
            WhatsAppInbox.phone_number,
            WhatsAppInbox.contact_name,
            func.count(WhatsAppInbox.id).label('unread_count'),
            func.max(WhatsAppInbox.incoming_time).label('last_unread_time')
        ).filter(
            WhatsAppInbox.device_id.in_(device_ids),
            WhatsAppInbox.chat_type == "individual",  # ONLY individual messages, no groups
            WhatsAppInbox.is_read == False,          # Must be unread
            WhatsAppInbox.is_outgoing == False      # Only incoming messages
        ).group_by(
            WhatsAppInbox.phone_number,
            WhatsAppInbox.contact_name
        ).order_by(
            func.max(WhatsAppInbox.incoming_time).desc()
        ).all()

        total_unread = sum(count.unread_count for count in unread_counts)

        logger.info(f"[REPLIES] Unread count: {total_unread} across {len(unread_counts)} contacts from ALL devices (individual only)")
        
        # Log each contact with unread for debugging
        for count in unread_counts:
            logger.info(f"[REPLIES] Contact unread: {count.contact_name or count.phone_number} - {count.unread_count} messages")

        return {
            "success": True,
            "data": [
                {
                    "phone_number": count.phone_number,
                    "contact_name": count.contact_name or count.phone_number,
                    "unread_count": count.unread_count,
                    "last_unread_time": count.last_unread_time
                }
                for count in unread_counts
            ],
            "total_unread": total_unread
        }

    except Exception as e:
        logger.error(f"Error getting unread count: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/active-devices")
async def get_active_devices(
    current_user: BusiUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Return only CONNECTED web devices with message counts."""
    from models.device import DeviceType
    from sqlalchemy import func
    
    # Get user's web devices that are marked 'connected' in DB
    db_devices = db.query(Device).filter(
        Device.busi_user_id == current_user.busi_user_id,
        Device.device_type == DeviceType.web,
        Device.session_status == "connected"
    ).all()
    
    # LIVE VERIFICATION: Cross-check with engine to ensure status is real
    from services.unified_whatsapp_sender import unified_sender
    
    devices = []
    for d in db_devices:
        engine_status = unified_sender.get_device_status(str(d.device_id))
        if engine_status == "connected":
            devices.append(d)
        else:
            # Sync DB with reality: Mark as disconnected if engine says so
            logger.warning(f"[REPLIES] Device {d.device_id} marked connected in DB but engine says '{engine_status}'. Syncing status.")
            d.session_status = "disconnected"
            db.commit()
    
    # Get message counts for each device
    device_data = []
    for device in devices:
        # Count total messages for this device
        message_count = db.query(func.count(WhatsAppInbox.id)).filter(
            WhatsAppInbox.device_id == device.device_id,
            WhatsAppInbox.chat_type == "individual"
        ).scalar() or 0
        
        # Count unread messages for this device
        unread_count = db.query(func.count(WhatsAppInbox.id)).filter(
            WhatsAppInbox.device_id == device.device_id,
            WhatsAppInbox.chat_type == "individual",
            WhatsAppInbox.is_read == False,
            WhatsAppInbox.is_outgoing == False
        ).scalar() or 0
        
        device_data.append({
            "device_id": str(device.device_id),
            "device_name": device.device_name or f"Device {str(device.device_id)[:8]}",
            "session_status": device.session_status.value if hasattr(device.session_status, "value") else str(device.session_status),
            "is_connected": str(device.session_status).lower() in ["connected", "sessionstatus.connected"],
            "message_count": message_count,
            "unread_count": unread_count,
            "last_activity": device.last_active or device.created_at
        })
    
    return {
        "success": True,
        "data": device_data
    }


@router.get("", response_model=InboxResponse)
async def get_inbox_messages(
    device_id: Optional[str] = None,
    current_user: BusiUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Fetch inbox messages for CONNECTED devices only.
    Shows only active/connected device chats, not disconnected devices.
    """
    try:
        from models.device import DeviceType
        from sqlalchemy import or_, and_

        # 1. Get user's CONNECTED web devices only
        if device_id:
            device = db.query(Device).filter(
                Device.device_id == device_id,
                Device.busi_user_id == current_user.busi_user_id,
                Device.device_type == DeviceType.web,
                Device.session_status == "connected"  # Must be connected
            ).first()
            if not device:
                raise HTTPException(status_code=404, detail="Connected device not found or not accessible")
            device_ids = [device.device_id]
        else:
            # STRICT FILTER: Only show messages from currently connected devices
            # This keeps the workspace clean as requested
            db_devices = db.query(Device).filter(
                Device.busi_user_id == current_user.busi_user_id,
                Device.device_type == DeviceType.web,
                Device.session_status == "connected"
            ).all()
            
            from services.unified_whatsapp_sender import unified_sender
            device_ids = []
            for d in db_devices:
                # Double-verify with engine to ensure status is real
                if unified_sender.get_device_status(str(d.device_id)) == "connected":
                    device_ids.append(d.device_id)
                else:
                    # Sync DB with reality
                    d.session_status = "disconnected"
                    db.commit()

        logger.info(f"[REPLIES] Inbox fetch user={current_user.busi_user_id} device_filter={device_id} connected_devices={len(device_ids)}")

        if not device_ids:
            return {"success": True, "data": []}

        # 2. Define windows (30 days history + ALWAYS show unread)
        # Extended from 7 days to 30 days to preserve longer chat history
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)

        # 🎯 ACTIVE DEVICES ONLY: Fetch messages from connected devices only
        # We fetch: (Recent history within 30 days) OR (Any unread incoming message regardless of time)
        # This ensures only active device chats are shown
        messages = db.query(WhatsAppInbox).filter(
            WhatsAppInbox.device_id.in_(device_ids),
            WhatsAppInbox.chat_type == "individual",
            or_(
                WhatsAppInbox.incoming_time >= thirty_days_ago,  # Extended history window
                and_(
                    WhatsAppInbox.is_read == False,              # OR Unread incoming
                    WhatsAppInbox.is_outgoing == False
                )
            )
        ).order_by(WhatsAppInbox.incoming_time.desc()).all()  # Most recent first

        logger.info(f"[REPLIES] Inbox items found={len(messages)} from connected devices")

        response_data = []
        needs_commit = False

        for msg in messages:
            # SAFETY & DB HEALING
            clean_phone = normalize_phone(msg.phone_number)
            if not clean_phone:
                continue

            if clean_phone != msg.phone_number:
                msg.phone_number = clean_phone
                needs_commit = True

            # Requirements D: Outgoing rows must ALWAYS be is_read = True
            if msg.is_outgoing and not msg.is_read:
                msg.is_read = True
                needs_commit = True

            # Serialize and apply web-only unread flag logic (Matches Requirement A)
            try:
                # Add TZ info for browser consistency
                if msg.incoming_time and msg.incoming_time.tzinfo is None:
                    msg.incoming_time = msg.incoming_time.replace(tzinfo=timezone.utc)
                if msg.reply_time and msg.reply_time.tzinfo is None:
                    msg.reply_time = msg.reply_time.replace(tzinfo=timezone.utc)

                msg_dict = InboxMessageResponse.model_validate(msg)
                
                # Computed Flags for Frontend Layout (Requirement E)
                msg_dict.is_incoming = not msg.is_outgoing
                
                # Unread is WEB-ONLY logic (Requirement 1, 6)
                # Outgoing messages never count as unread.
                msg_dict.unread = (not msg.is_read) and (not msg.is_outgoing)
                
                response_data.append(msg_dict)
            except Exception as val_err:
                logger.error(f"[REPLIES] Message {msg.id} serialization error: {val_err}")
                continue

        if needs_commit:
            db.commit()

        return {"success": True, "data": response_data}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching inbox: {e}")
        raise HTTPException(status_code=500, detail=str(e))



# ---------------------------------------------------
# SEND REPLY
# ---------------------------------------------------
@router.post("/send")
async def send_reply(
    request: ReplyRequest,
    current_user: BusiUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # 1. Validate Phone
        phone = normalize_phone(request.phone)
        if not phone:
            raise HTTPException(status_code=400, detail=f"Invalid phone number: {request.phone}")

        # SAFETY FIREWALL: Block obvious IDs but allow legitimate international numbers
        if len(phone) > 20:
             logger.critical(f"[SAFETY FIREWALL] BLOCKED attempt to send to ID-like phone: {phone}")
             raise HTTPException(status_code=400, detail=f"Invalid phone/JID detection (Length > 20). Sending blocked.")

        # 2. Validate Key Props
        if not request.device_id:
             raise HTTPException(status_code=400, detail="Device ID is required")

        # 3. Optional: Link to Inbox Message if ID provided
        inbox_msg = None
        if request.message_id:
            inbox_msg = db.query(WhatsAppInbox).filter(
                WhatsAppInbox.id == request.message_id
            ).first()

            if inbox_msg:
                # Security check: Ensure device matches
                if str(inbox_msg.device_id) != request.device_id:
                     logger.warning(f"Device mismatch for message {request.message_id}: msg_device={inbox_msg.device_id}, req_device={request.device_id}")
                     raise HTTPException(status_code=400, detail="Device mismatch for this message.")
        
        # 4. Check Device Status (using requested device_id)
        from services.unified_whatsapp_sender import unified_sender
        
        # Verify device exists in DB first
        device = db.query(Device).filter(
            Device.device_id == request.device_id,
            Device.busi_user_id == current_user.busi_user_id
        ).first()

        if not device:
            raise HTTPException(status_code=403, detail="Unauthorized or invalid device")

        engine_status = unified_sender.get_device_status(str(device.device_id))

        if engine_status in [None, "not_found", "disconnected"]:
            from models.device import DeviceType

            logger.warning(f"[REPLIES] Requested device {device.device_id} is '{engine_status}' in engine.")
            logger.info(f"[REPLIES] Searching for any other connected web devices for user {current_user.busi_user_id}")

            web_devices = db.query(Device).filter(
                Device.busi_user_id == current_user.busi_user_id,
                Device.device_type == DeviceType.web,
                Device.device_id != device.device_id
            ).all()

            resolved = None
            for d in web_devices:
                status = unified_sender.get_device_status(str(d.device_id))
                logger.info(f"[REPLIES] Checking alternative device {d.device_id}: {status}")
                if status == "connected":
                    resolved = d
                    break

            if resolved:
                logger.warning(
                    f"[REPLIES] AUTO-RESOLVED: {device.device_id} → {resolved.device_id} (connected)"
                )
                device = resolved
                engine_status = "connected"
            else:
                logger.info(f"[REPLIES] No alternative connected devices found. Proceeding with current device anyway.")
                # We don't raise 400 here anymore; we let unified_sender try the actual delivery.
                # Transient "disconnected" statuses in the engine can sometimes still deliver messages.

        logger.info(f"[REPLIES] Sending reply to {phone} via device {device.device_id}")
        logger.info(f"[REPLIES] Message content: {request.reply_text[:100]}...")

        target_jid = inbox_msg.remote_jid if inbox_msg else None
        
        result = send_whatsapp_message(
            device_id=str(device.device_id),
            phone=phone,
            message=request.reply_text,
            jid=target_jid
        )

        logger.info(f"[REPLIES] Send result: {result}")

        if not result.get("success"):
            logger.error(f"[REPLIES] Send failed: {result.get('error')}")
            raise HTTPException(status_code=400, detail=result.get("error"))

        # 5. Record sent reply as a new outgoing row in the inbox
        # This makes it visible in the conversation thread when UI refreshes
        now = datetime.now(timezone.utc)
        
        logger.info(f"[REPLIES] Recording outgoing message in inbox...")
        
        # Determine contact name (falling back to any previous record for this phone)
        contact_name = inbox_msg.contact_name if inbox_msg else None
        if not contact_name:
            prev_msg = db.query(WhatsAppInbox).filter(
                WhatsAppInbox.phone_number == phone
            ).first()
            if prev_msg:
                contact_name = prev_msg.contact_name

        sent_row = WhatsAppInbox(
            device_id=device.device_id,
            phone_number=phone,
            contact_name=contact_name,
            chat_type="individual",
            incoming_message=request.reply_text,   # outgoing text stored here
            message_id=result.get("message_id"),
            incoming_time=now,
            is_read=True,
            is_replied=True,           # Flag: this row IS a sent/reply message
            is_outgoing=True,          # Mark explicitly as outgoing
            reply_message=request.reply_text,
            reply_time=now,
        )
        db.add(sent_row)
        logger.info(f"[REPLIES] Added outgoing message row for {phone}")

        # Also mark the original incoming message as replied (if linked)
        if inbox_msg:
            logger.info(f"[REPLIES] Marking original message {inbox_msg.id} as replied")
            inbox_msg.is_replied = True
            inbox_msg.reply_message = request.reply_text
            inbox_msg.reply_time = now
            inbox_msg.phone_number = phone

        db.commit()
        logger.info(f"[REPLIES] Database commit completed. Message ID: {result.get('message_id')}")

        return {
            "status": "success",
            "message_id": result.get("message_id"),
            "delivery_status": result.get("status"),
            "device_used": str(device.device_id),
            "phone_sent_to": phone
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reply send error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------
# MARK READ
# ---------------------------------------------------
from schemas.whatsapp_inbox import MarkReadRequest

@router.post("/mark-read")
async def mark_conversations_read(
    request: MarkReadRequest,
    current_user: BusiUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark messages as read FOR A SPECIFIC DEVICE (Requirement C).
    - isolation: device_id
    - filter: incoming messages only (is_outgoing = false)
    """
    try:
        from models.device import DeviceType
        
        # 1. Device Isolation (Requirement C)
        # Verify the requested device_id belongs to the user and is a web device
        if request.device_id:
            device = db.query(Device).filter(
                Device.device_id == request.device_id,
                Device.busi_user_id == current_user.busi_user_id,
                Device.device_type == DeviceType.web
            ).first()
            if not device:
                raise HTTPException(status_code=404, detail="Device not found or access denied")
            target_device_ids = [device.device_id]
        else:
            # Fallback for all user's web devices (if not provided)
            user_devices = db.query(Device).filter(
                Device.busi_user_id == current_user.busi_user_id,
                Device.device_type == DeviceType.web
            ).all()
            target_device_ids = [d.device_id for d in user_devices]

        if not target_device_ids:
             return {"status": "success", "updated_count": 0}

        # 2. Update logic (Requirement C, D)
        # Only mark incoming messages as read. Outgoing are read by default.
        updated_count = db.query(WhatsAppInbox).filter(
            WhatsAppInbox.device_id.in_(target_device_ids),
            WhatsAppInbox.phone_number == request.phone_number,
            WhatsAppInbox.is_outgoing == False,
            WhatsAppInbox.is_read == False
        ).update({"is_read": True}, synchronize_session=False)
        
        db.commit()
        logger.info(f"[REPLIES] Marked {updated_count} incoming messages read for device(s) {target_device_ids}")
        return {"status": "success", "updated_count": updated_count}
    except Exception as e:
        logger.error(f"Error marking as read: {e}")
        raise HTTPException(status_code=500, detail=str(e))
