from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime, timezone

from db.session import get_db
from models.busi_user import BusiUser
from models.device import Device, DeviceType
from models.whatsapp_messages import WhatsAppMessages
from api.auth import get_current_user
from services.baileys_message_sync_service import baileys_sync_service
from services.uuid_service import UUIDService
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/messages",
    tags=["Messages"]
)

# Pydantic models for request/response
class MessageStoreRequest(BaseModel):
    device_id: str
    phone: str
    message_id: str
    message: str
    timestamp: Optional[datetime] = None
    from_me: bool = False
    contact_name: Optional[str] = None
    message_type: str = "text"
    remote_jid: Optional[str] = None
    chat_type: str = "individual"

class MessageStoreResponse(BaseModel):
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None

class ConversationResponse(BaseModel):
    phone: str
    contact_name: str
    last_message: str
    last_message_time: datetime
    unread_count: int
    total_messages: int

class ConversationsListResponse(BaseModel):
    success: bool
    data: List[ConversationResponse]
    total_conversations: int

class MessagesListResponse(BaseModel):
    success: bool
    data: List[Dict[str, Any]]
    total_messages: int
    page: int
    per_page: int

@router.post("/store", response_model=MessageStoreResponse)
async def store_message(
    request: MessageStoreRequest,
    background_tasks: BackgroundTasks,
    current_user: BusiUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Store a WhatsApp message in the database.
    Handles deduplication and device isolation.
    """
    try:
        # Validate device belongs to user
        device_uuid = UUIDService.safe_convert(request.device_id)
        device = db.query(Device).filter(
            Device.device_id == device_uuid,
            Device.busi_user_id == current_user.busi_user_id
        ).first()
        
        if not device:
            raise HTTPException(status_code=404, detail="Device not found or not accessible")
        
        # Check for duplicates using message_id
        existing_message = db.query(WhatsAppMessages).filter(
            WhatsAppMessages.message_id == request.message_id
        ).first()
        
        if existing_message:
            logger.info(f"Message {request.message_id} already exists, skipping")
            return MessageStoreResponse(
                success=True,
                message_id=existing_message.message_id
            )
        
        # Create new message record
        new_message = WhatsAppMessages(
            device_id=device_uuid,
            message_id=request.message_id,
            remote_jid=request.remote_jid,
            phone=request.phone,
            contact_name=request.contact_name,
            message=request.message,
            message_type=request.message_type,
            timestamp=request.timestamp or datetime.now(timezone.utc),
            from_me=request.from_me,
            is_read=request.from_me,  # Outgoing messages are read by default
            chat_type=request.chat_type
        )
        
        db.add(new_message)
        db.commit()
        db.refresh(new_message)
        
        logger.info(f"Stored message {request.message_id} for device {request.device_id}")
        
        return MessageStoreResponse(
            success=True,
            message_id=new_message.message_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error storing message: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations", response_model=ConversationsListResponse)
async def get_conversations(
    device_id: Optional[str] = Query(None, description="Filter by specific device"),
    limit: int = Query(50, ge=1, le=200, description="Number of conversations to fetch"),
    current_user: BusiUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get conversation summary for the user's devices.
    Shows only active device messages with unread counts.
    """
    try:
        # Get user's devices (filter by device_id if provided)
        if device_id:
            device_uuid = UUIDService.safe_convert(device_id)
            device = db.query(Device).filter(
                Device.device_id == device_uuid,
                Device.busi_user_id == current_user.busi_user_id,
                Device.device_type == DeviceType.web
            ).first()
            
            if not device:
                raise HTTPException(status_code=404, detail="Device not found or not accessible")
            
            device_ids = [device_uuid]
        else:
            # Get all user's web devices
            devices = db.query(Device).filter(
                Device.busi_user_id == current_user.busi_user_id,
                Device.device_type == DeviceType.web
            ).all()
            device_ids = [d.device_id for d in devices]
        
        if not device_ids:
            return ConversationsListResponse(
                success=True,
                data=[],
                total_conversations=0
            )
        
        # Query conversation summary
        conversations_query = db.query(
            WhatsAppMessages.phone,
            func.max(WhatsAppMessages.contact_name).label('contact_name'),
            func.max(WhatsAppMessages.message).label('last_message'),
            func.max(WhatsAppMessages.timestamp).label('last_message_time'),
            func.sum(
                func.case(
                    (and_(WhatsAppMessages.is_read == False, WhatsAppMessages.from_me == False), 1),
                    else_=0
                )
            ).label('unread_count'),
            func.count(WhatsAppMessages.id).label('total_messages')
        ).filter(
            WhatsAppMessages.device_id.in_(device_ids),
            WhatsAppMessages.chat_type == "individual"
        ).group_by(
            WhatsAppMessages.phone
        ).order_by(
            desc(func.max(WhatsAppMessages.timestamp))
        ).limit(limit)
        
        conversations = conversations_query.all()
        
        # Format response
        conversation_list = []
        for conv in conversations:
            conversation_list.append(ConversationResponse(
                phone=conv.phone,
                contact_name=conv.contact_name or conv.phone,
                last_message=conv.last_message or "",
                last_message_time=conv.last_message_time,
                unread_count=conv.unread_count or 0,
                total_messages=conv.total_messages
            ))
        
        return ConversationsListResponse(
            success=True,
            data=conversation_list,
            total_conversations=len(conversation_list)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversation/{phone}", response_model=MessagesListResponse)
async def get_conversation_messages(
    phone: str,
    device_id: Optional[str] = Query(None, description="Filter by specific device"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Messages per page"),
    current_user: BusiUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all messages for a specific conversation (phone number).
    Supports pagination and device filtering.
    """
    try:
        # Get user's devices
        if device_id:
            device_uuid = UUIDService.safe_convert(device_id)
            device = db.query(Device).filter(
                Device.device_id == device_uuid,
                Device.busi_user_id == current_user.busi_user_id,
                Device.device_type == DeviceType.web
            ).first()
            
            if not device:
                raise HTTPException(status_code=404, detail="Device not found or not accessible")
            
            device_ids = [device_uuid]
        else:
            devices = db.query(Device).filter(
                Device.busi_user_id == current_user.busi_user_id,
                Device.device_type == DeviceType.web
            ).all()
            device_ids = [d.device_id for d in devices]
        
        if not device_ids:
            return MessagesListResponse(
                success=True,
                data=[],
                total_messages=0,
                page=page,
                per_page=per_page
            )
        
        # Query messages with pagination
        offset = (page - 1) * per_page
        
        messages_query = db.query(WhatsAppMessages).filter(
            WhatsAppMessages.device_id.in_(device_ids),
            WhatsAppMessages.phone == phone,
            WhatsAppMessages.chat_type == "individual"
        ).order_by(
            desc(WhatsAppMessages.timestamp)
        ).offset(offset).limit(per_page)
        
        messages = messages_query.all()
        
        # Get total count for pagination
        total_count = db.query(func.count(WhatsAppMessages.id)).filter(
            WhatsAppMessages.device_id.in_(device_ids),
            WhatsAppMessages.phone == phone,
            WhatsAppMessages.chat_type == "individual"
        ).scalar() or 0
        
        # Format response
        message_list = []
        for msg in messages:
            message_list.append(msg.to_dict())
        
        return MessagesListResponse(
            success=True,
            data=message_list,
            total_messages=total_count,
            page=page,
            per_page=per_page
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching conversation messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/mark-read")
async def mark_conversation_read(
    phone: str,
    device_id: Optional[str] = None,
    current_user: BusiUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark all messages in a conversation as read.
    Only marks incoming messages as read.
    """
    try:
        # Get user's devices
        if device_id:
            device_uuid = UUIDService.safe_convert(device_id)
            device = db.query(Device).filter(
                Device.device_id == device_uuid,
                Device.busi_user_id == current_user.busi_user_id,
                Device.device_type == DeviceType.web
            ).first()
            
            if not device:
                raise HTTPException(status_code=404, detail="Device not found or not accessible")
            
            device_ids = [device_uuid]
        else:
            devices = db.query(Device).filter(
                Device.busi_user_id == current_user.busi_user_id,
                Device.device_type == DeviceType.web
            ).all()
            device_ids = [d.device_id for d in devices]
        
        if not device_ids:
            return {"success": True, "updated_count": 0}
        
        # Update unread incoming messages
        updated_count = db.query(WhatsAppMessages).filter(
            WhatsAppMessages.device_id.in_(device_ids),
            WhatsAppMessages.phone == phone,
            WhatsAppMessages.from_me == False,
            WhatsAppMessages.is_read == False
        ).update({"is_read": True}, synchronize_session=False)
        
        db.commit()
        
        logger.info(f"Marked {updated_count} messages as read for conversation {phone}")
        
        return {
            "success": True,
            "updated_count": updated_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking messages as read: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/unread-count")
async def get_unread_count(
    device_id: Optional[str] = None,
    current_user: BusiUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get total unread message count for the user.
    Perfect for badges and notifications.
    """
    try:
        # Get user's devices
        if device_id:
            device_uuid = UUIDService.safe_convert(device_id)
            device = db.query(Device).filter(
                Device.device_id == device_uuid,
                Device.busi_user_id == current_user.busi_user_id,
                Device.device_type == DeviceType.web
            ).first()
            
            if not device:
                raise HTTPException(status_code=404, detail="Device not found or not accessible")
            
            device_ids = [device_uuid]
        else:
            devices = db.query(Device).filter(
                Device.busi_user_id == current_user.busi_user_id,
                Device.device_type == DeviceType.web
            ).all()
            device_ids = [d.device_id for d in devices]
        
        if not device_ids:
            return {"success": True, "total_unread": 0}
        
        # Count unread incoming messages
        unread_count = db.query(func.count(WhatsAppMessages.id)).filter(
            WhatsAppMessages.device_id.in_(device_ids),
            WhatsAppMessages.chat_type == "individual",
            WhatsAppMessages.from_me == False,
            WhatsAppMessages.is_read == False
        ).scalar() or 0
        
        return {
            "success": True,
            "total_unread": unread_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting unread count: {e}")
        raise HTTPException(status_code=500, detail=str(e))
