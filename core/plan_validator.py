from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from models.busi_user import BusiUser
from models.reseller import Reseller
import uuid

def check_busi_user_plan(db: Session, busi_user_id: str):
    """
    Checks if a business user has a valid plan and remaining credits.
    Raises HTTPException if not.
    """
    user = db.query(BusiUser).filter(BusiUser.busi_user_id == busi_user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business user not found"
        )
    
    # 1. Check Plan Expiry
    # 🔥 FIX: If user has plan_name and credits, allow even if plan_expiry is not set
    # This handles cases where plan_expiry wasn't set properly during purchase
    if not user.plan_expiry:
        if not user.plan_name or (user.credits_remaining or 0) <= 0:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No active plan found. Please purchase a plan to continue."
            )
        # If they have plan_name and credits, skip expiry check
    else:
        # Robust comparison: Ensure both are aware or both are naive
        now = datetime.now(timezone.utc)
        plan_expiry = user.plan_expiry
        if plan_expiry.tzinfo is None:
            plan_expiry = plan_expiry.replace(tzinfo=timezone.utc)

        if plan_expiry < now:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your plan has expired. Please renew your plan to continue."
            )
    
    # 2. Check Credits
    credits_remaining = user.credits_remaining or 0
    
    # 🔥 FIX: If table shows 0, do a secondary real-time check against logs
    # This prevents blocking users if the table sync failed but logs show available credits
    if credits_remaining <= 0:
        from models.message_usage import MessageUsageCreditLog
        from sqlalchemy import func
        
        allocated = float(user.credits_allocated or 0)
        used = db.query(func.sum(MessageUsageCreditLog.credits_deducted)).filter(
            MessageUsageCreditLog.busi_user_id == str(busi_user_id),
            MessageUsageCreditLog.credits_deducted > 0
        ).scalar() or 0
        
        real_remaining = max(0, allocated - used)
        
        if real_remaining > 0:
            # Auto-reconcile the table value for future fast lookups
            user.credits_remaining = real_remaining
            user.credits_used = used
            db.commit()
            credits_remaining = real_remaining
            
    if credits_remaining <= 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient credits. Please recharge your wallet to continue."
        )
    
    return user

def check_reseller_plan(db: Session, reseller_id: str):
    """
    Checks if a reseller has a valid plan and remaining credits.
    Raises HTTPException if not.
    """
    reseller = db.query(Reseller).filter(Reseller.reseller_id == reseller_id).first()
    if not reseller:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reseller not found"
        )
    
    # 1. Check Plan Expiry
    if not reseller.plan_expiry:
         # Resellers might not have a "plan" in the same way, but they need credits
         pass
    else:
        now = datetime.now(timezone.utc)
        plan_expiry = reseller.plan_expiry
        if plan_expiry.tzinfo is None:
            plan_expiry = plan_expiry.replace(tzinfo=timezone.utc)

        if plan_expiry < now:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your reseller plan has expired. Please contact admin."
            )
    
    # 2. Check Credits (Available credits for allocation)
    if (reseller.available_credits or 0) <= 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient credits in reseller wallet. Please purchase more credits to allocate."
        )
    
    return reseller
