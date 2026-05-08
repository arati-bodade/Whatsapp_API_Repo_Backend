from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import uuid

from db.session import get_db
from schemas.message_usage import (
    MessageUsageCreditLogCreate,
    MessageUsageCreditLogResponse,
    MessageUsageCreditLogUpdate
)
from services.message_usage_service import MessageUsageService

router = APIRouter()


@router.post("/", response_model=MessageUsageCreditLogResponse)
async def create_usage_log(
    usage_data: MessageUsageCreditLogCreate,
    db: Session = Depends(get_db)
):
    """Create a new message usage credit log entry."""
    service = MessageUsageService(db)
    
    # Create usage log with auto-generated usage_id and user type detection
    result = service.create_usage_log(usage_data)
    
    return result


@router.get("/{usage_id}", response_model=MessageUsageCreditLogResponse)
async def get_usage_log(
    usage_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific usage log by ID."""
    service = MessageUsageService(db)
    usage_log = service.get_usage_log(usage_id)
    
    if not usage_log:
        raise HTTPException(status_code=404, detail="Usage log not found")
    
    return usage_log


@router.get("/user/{busi_user_id}", response_model=List[MessageUsageCreditLogResponse])
async def get_user_usage_logs(
    busi_user_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """Get usage logs for a specific user with optional date filtering."""
    service = MessageUsageService(db)
    return service.get_user_usage_logs(
        busi_user_id=busi_user_id,
        skip=skip,
        limit=limit,
        start_date=start_date,
        end_date=end_date
    )


@router.put("/{usage_id}", response_model=MessageUsageCreditLogResponse)
async def update_usage_log(
    usage_id: str,
    usage_data: MessageUsageCreditLogUpdate,
    db: Session = Depends(get_db)
):
    """Update a usage log entry."""
    service = MessageUsageService(db)
    updated_log = service.update_usage_log(usage_id, usage_data)
    
    if not updated_log:
        raise HTTPException(status_code=404, detail="Usage log not found")
    
    return updated_log


@router.delete("/{usage_id}")
async def delete_usage_log(
    usage_id: str,
    db: Session = Depends(get_db)
):
    """Delete a usage log entry."""
    service = MessageUsageService(db)
    success = service.delete_usage_log(usage_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Usage log not found")
    
    return {"message": "Usage log deleted successfully"}


@router.get("/user/{busi_user_id}/balance", response_model=dict)
async def get_user_balance(
    busi_user_id: str,
    db: Session = Depends(get_db)
):
    """Get current balance for a user based on their latest usage log."""
    service = MessageUsageService(db)
    balance = service.get_user_current_balance(busi_user_id)
    
    return {"user_id": busi_user_id, "current_balance": balance}


@router.get("/user/{busi_user_id}/type", response_model=dict)
async def get_user_type(
    busi_user_id: str,
    db: Session = Depends(get_db)
):
    """Get user type (reseller or business)."""
    service = MessageUsageService(db)
    user_type = service.get_user_type(busi_user_id)
    
    return {"user_id": busi_user_id, "user_type": user_type, "description": f"User is identified as {user_type}"}
