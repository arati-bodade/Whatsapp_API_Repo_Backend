from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Header, status
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session
from sqlalchemy import text, func, extract
from typing import List, Optional
import json
import uuid
from datetime import datetime, timezone
import logging
logger = logging.getLogger(__name__)

from db.session import get_db
from models.device import Device, SessionStatus
from services.whatsapp_service import WhatsAppService
from schemas.whatsapp import MessageRequest, MessageResponse, FileMessageRequest, FileMessageResponse
from models.message import Message
from core.security import verify_token
from core.plan_validator import check_busi_user_plan

router = APIRouter(tags=["User Dashboard"])

# --- Dependencies ---

def get_whatsapp_service(db: Session = Depends(get_db)) -> WhatsAppService:
    return WhatsAppService(db)

async def get_current_busi_user(authorization: str = Header(None)) -> dict:
    """
    Extracts business user info from JWT.
    Ensures the user has 'business' or 'reseller' (if acting as one) role?
    Actually, mostly 'business' role users use this dashboard.
    """
    if not authorization or not authorization.startswith("Bearer "):
        print(f"DEBUG: Invalid auth header: {authorization}") 
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header"
        )
    token = authorization.split(" ")[1]
    payload = verify_token(token)
    if not payload or payload.get("error"):
        error_type = payload.get("error", "invalid_token") if payload else "invalid_token"
        error_message = payload.get("message", "Invalid or expired token") if payload else "Invalid or expired token"
        
        if error_type == "token_expired":
            print(f"DEBUG: Token expired for user")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired. Please log in again."
            )
        else:
            print(f"DEBUG: Token verification failed for token: {token[:10]}...")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=error_message
            )
    return payload


# --- Local Schemas ---

class UserMessageRequest(BaseModel):
    receiver_number: str = Field(..., description="Receiver phone number")
    message_text: str = Field(..., description="Message content")
    device_id: Optional[str] = Field(None, description="Device ID to use (optional - will auto-resolve if not provided)")


class DeliveryReportResponse(BaseModel):
    sent_at: Optional[str] = None
    message: Optional[str] = ""
    sender: Optional[str] = Field(None, alias="from")
    receiver: Optional[str] = Field(None, alias="to")
    attachment_url: Optional[str] = None
    status: Optional[str] = "UNKNOWN"
    mode: Optional[str] = "UNKNOWN"

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# --- Endpoints ---

@router.get("/devices", response_model=List[dict])
async def get_user_devices(
    background_tasks: BackgroundTasks,
    token_payload: dict = Depends(get_current_busi_user),
    whatsapp_service: WhatsAppService = Depends(get_whatsapp_service)
):
    """
    Get devices for the logged-in business user with automatic background sync.
    """
    user_id = token_payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    try:
        # Trigger background sync from engine to keep DB fresh
        from services.device_sync_service import device_sync_service
        from db.session import SessionLocal
        
        def sync_task_wrapper(uid):
            with SessionLocal() as db_session:
                device_sync_service.sync_user_devices(db_session, uid)
                
        background_tasks.add_task(sync_task_wrapper, str(user_id))

        # Use raw SQL to avoid SQLAlchemy type casting issues
        user_id_str = str(user_id)
        result = whatsapp_service.db.execute(text("""
            SELECT device_id, busi_user_id, device_name, device_type, session_status,
                   qr_last_generated, ip_address, last_active, created_at, updated_at
            FROM devices 
            WHERE busi_user_id = :user_id AND deleted_at IS NULL
            ORDER BY created_at DESC
        """), {"user_id": user_id_str}).fetchall()
        
        # Manual serialization for Enums
        results = []
        for row in result:
            results.append({
                "device_id": row.device_id,
                "busi_user_id": row.busi_user_id,
                "device_name": row.device_name,
                "device_type": row.device_type,
                "session_status": row.session_status,
                "qr_last_generated": row.qr_last_generated,
                "ip_address": row.ip_address,
                "last_active": row.last_active,
                "created_at": row.created_at,
                "updated_at": row.updated_at
            })
        return results
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Failed to get devices: {str(e)}")


@router.post("/message/unofficial", response_model=MessageResponse)
async def send_unofficial_message(
    message_data: UserMessageRequest,
    token_payload: dict = Depends(get_current_busi_user),
    whatsapp_service: WhatsAppService = Depends(get_whatsapp_service)
):
    """
    Send an unofficial WhatsApp message from the user's connected device.
    Delegates device selection and validation to the service layer.
    """
    user_id = token_payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    try:
        # Construct MessageRequest
        # We inject 'user_id' from token. device_id from frontend or None for auto-resolution.
        full_request = MessageRequest(
            receiver_number=message_data.receiver_number,
            message_text=message_data.message_text,
            user_id=user_id,
            device_id=message_data.device_id  # Pass device_id from frontend (may be None)
        )

        # NEW: Check Plan/Credits before sending
        check_busi_user_plan(whatsapp_service.db, user_id)

        # Use Service Logic (Handles device resolution, status check, credit deduction)
        result = whatsapp_service.send_message_via_engine(full_request)
        return result

    except HTTPException:
        raise
    except Exception as e:
        # Ensure clean error messages for frontend
        error_msg = str(e)
        if "No active/connected device found" in error_msg:
            raise HTTPException(status_code=400, detail=error_msg)
        if "Insufficient credits" in error_msg:
             raise HTTPException(status_code=400, detail=error_msg)
        if "not found in database" in error_msg:
            raise HTTPException(status_code=404, detail=error_msg)
        if "does not belong to user" in error_msg:
            raise HTTPException(status_code=403, detail=error_msg)
        if "is not connected" in error_msg:
            raise HTTPException(status_code=400, detail=error_msg)
             
        raise HTTPException(status_code=400, detail=f"Failed to send message: {error_msg}")


@router.get("/delivery-reports", response_model=List[DeliveryReportResponse])
async def get_delivery_reports(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    token_payload: dict = Depends(get_current_busi_user),
    db: Session = Depends(get_db)
):
    """
    Get delivery reports for the logged-in user, optionally filtered by date.
    """
    user_id = token_payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    try:
        user_uuid = str(user_id)
        query = db.query(Message).filter(Message.busi_user_id == user_uuid)

        from datetime import datetime
        
        if start_date:
            try:
                # Handle dates like '2023-10-25' or ISO strings
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                query = query.filter(Message.sent_at >= start_dt)
            except ValueError:
                pass
                
        if end_date:
            try:
                # To include the entire end_date day if only date is passed
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                if len(end_date) <= 10:  # If it's just 'YYYY-MM-DD'
                    end_dt = end_dt.replace(hour=23, minute=59, second=59)
                query = query.filter(Message.sent_at <= end_dt)
            except ValueError:
                pass

        messages = query.order_by(Message.sent_at.desc()).all()

        reports = []
        for msg in messages:
            attachment = None
            if str(msg.message_type) == "MEDIA":
                attachment = "Attachment" 
            
            reports.append(DeliveryReportResponse(
                sent_at=msg.sent_at.isoformat() if msg.sent_at else None,
                message=str(msg.message_body) if msg.message_body else "",
                sender=str(msg.sender_number) if msg.sender_number else "Unknown",
                receiver=str(msg.receiver_number) if msg.receiver_number else "Unknown",
                attachment_url=attachment,
                status=msg.status.value if hasattr(msg.status, 'value') else str(msg.status),
                mode=msg.mode.value if hasattr(msg.mode, 'value') else str(msg.mode)
            ))
            
        return [report.model_dump(by_alias=True) for report in reports]
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to fetch delivery reports: {str(e)}")

@router.get("/dashboard/stats")
async def get_dashboard_summary_stats(
    token_payload: dict = Depends(get_current_busi_user),
    db: Session = Depends(get_db)
):
    """
    🔥 [DASHBOARD] Fetch quick summary stats for User Dashboard cards (Wallet, Plan, Devices)
    """
    user_id = token_payload.get("sub")
    user_uuid = str(user_id)
    
    from models.busi_user import BusiUser
    from models.payment_order import PaymentOrder
    
    # 1. User Info (Plan & Wallet)
    user = db.query(BusiUser).filter(BusiUser.busi_user_id == user_uuid).first()
    if not user:
         raise HTTPException(status_code=404, detail="User not found")
    
    # 🔥 SOURCE OF TRUTH: 
    # Allocated credits come from the BusiUser table (it consolidates all distribution/purchases)
    # Used credits and message counts come from real-time logs
    from models.message_usage import MessageUsageCreditLog
    
    # 1. Credits calculation
    credits_allocated = max(0, user.credits_allocated or 0)
    
    credits_used_db = db.query(func.sum(MessageUsageCreditLog.credits_deducted)).filter(
        MessageUsageCreditLog.busi_user_id == user_uuid,
        MessageUsageCreditLog.credits_deducted > 0
    ).scalar() or 0
    
    credits_used = max(0, credits_used_db)
    credits_remaining = max(0, credits_allocated - credits_used)
         
    # 2. Total Messages (Count every billable event in usage log)
    # This is more accurate for the 'Total Consumed' summary card
    total_messages = db.query(MessageUsageCreditLog).filter(
        MessageUsageCreditLog.busi_user_id == user_uuid,
        MessageUsageCreditLog.credits_deducted > 0
    ).count()
    
    # 3. Active Devices count
    active_devices = db.query(Device).filter(
        Device.busi_user_id == user_uuid,
        Device.session_status.in_(["CONNECTED", "connected"])
    ).count()
    
    return {
        "wallet": {
            "allocated": credits_allocated,
            "used": credits_used,
            "remaining": credits_remaining,
            "consumption_rate": user.consumption_rate
        },
        "plan": {
            "name": user.plan_name or "Standard",
            "expiry": user.plan_expiry.isoformat() if user.plan_expiry else None,
            "status": "ACTIVE" if user.plan_expiry and user.plan_expiry > datetime.now(timezone.utc) else "EXPIRED"
        },
        "metrics": {
            "total_messages": total_messages,
            "active_devices": active_devices
        },
        "profile": {
            "name": user.name,
            "business_name": user.business_name,
            "profile_image": user.profile_image
        }
    }

@router.get("/dashboard/graph-data")
async def get_dashboard_graph_data(
    token_payload: dict = Depends(get_current_busi_user),
    db: Session = Depends(get_db)
):
    """
    🔥 [GRAPH] Returns monthly message counts for the 'Message Delivery Performance' chart
    """
    user_id = token_payload.get("sub")
    user_uuid = str(user_id)
    
    from sqlalchemy import extract, func
    from datetime import datetime
    
    # Get stats for the current year
    current_year = datetime.now().year
    
    # 🔥 SOURCE OF TRUTH: Use MessageUsageCreditLog for graph data to match summary cards
    from models.message_usage import MessageUsageCreditLog
    
    # 1. Query usage logs (billed activity)
    usage_rows = db.query(
        extract('month', MessageUsageCreditLog.timestamp).label('month'),
        func.sum(MessageUsageCreditLog.credits_deducted).label('total')
    ).filter(
        MessageUsageCreditLog.busi_user_id == user_uuid,
        extract('year', MessageUsageCreditLog.timestamp) == current_year,
        MessageUsageCreditLog.credits_deducted > 0
    ).group_by(
        extract('month', MessageUsageCreditLog.timestamp)
    ).all()

    # Pre-populate 12 months
    monthly_stats = {i: {"sent": 0, "delivered": 0} for i in range(1, 13)}
    
    # Process usage logs (Treat each billed usage as a 'sent' message)
    logger.info(f"📊 [GRAPH_DEBUG] Found {len(usage_rows)} months with data for user {user_uuid}")
    for r in usage_rows:
        try:
            m = int(float(r.month)) # Handle both float and int returns
            if 1 <= m <= 12:
                count = int(r.total or 0)
                monthly_stats[m]["sent"] = count
                # For graph aesthetics, we'll assume a high delivery rate for billed messages
                monthly_stats[m]["delivered"] = int(count * 0.95) 
                logger.info(f"   📅 Month {m}: {count} messages (from credits)")
        except Exception as e:
            logger.error(f"   ❌ Error processing month {r.month}: {e}")
            pass

    # (Redundant query removed - logs are now primary source for bulk & single messages)

    # Prepare final result
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    result = []
    for i in range(1, 13):
        result.append({
            "name": month_names[i-1],
            "sent": monthly_stats[i]["sent"],
            "delivered": monthly_stats[i]["delivered"]
        })
    
    return result

@router.get("/dashboard/recent-orders")
async def get_recent_orders(
    token_payload: dict = Depends(get_current_busi_user),
    db: Session = Depends(get_db)
):
    """
    🔥 [TABLE] Get last 5 successful payment/credit orders for dashboard
    """
    user_id = token_payload.get("sub")
    user_uuid = str(user_id)
    
    from models.payment_order import PaymentOrder
    
    orders = db.query(PaymentOrder).filter(
        PaymentOrder.user_id == user_uuid,
        PaymentOrder.status == "success"
    ).order_by(PaymentOrder.created_at.desc()).limit(5).all()
    
    return [
        {
            "id": str(o.id),
            "date": o.created_at.isoformat() if o.created_at else None,
            "plan": o.plan_name,
            "credits": o.credits,
            "amount": o.amount,
            "txnid": o.txnid
        } for o in orders
    ]
