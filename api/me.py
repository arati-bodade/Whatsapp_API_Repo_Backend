from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any
import uuid

from db.session import get_db
from api.auth import get_current_user
from models.busi_user import BusiUser
from models.reseller import Reseller
from models.admin import MasterAdmin
from models.plan import Plan
from schemas.busi_user import PlanResponseSchema

router = APIRouter(tags=["Self"])

@router.get("/me/plan", response_model=dict)
async def get_my_plan(
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the current plan of the logged-in user (Business User, Reseller, or Admin).
    Standardized to prevent 403 errors across roles.
    """
    # 1. Handle Business Users
    if isinstance(current_user, BusiUser):
        # Fetch assigner name
        assigned_by_name = "Administrator"
        assigned_by_role = "admin"
        if current_user.parent_reseller_id:
            reseller = db.query(Reseller).filter(Reseller.reseller_id == current_user.parent_reseller_id).first()
            if reseller:
                assigned_by_name = reseller.name
                assigned_by_role = "reseller"

        # Auto-heal missing plan relationship
        user_plan = current_user.plan
        if not user_plan and getattr(current_user, 'plan_name', None):
            fetched_plan = db.query(Plan).filter(Plan.name == current_user.plan_name).first()
            if fetched_plan:
                current_user.plan_id = fetched_plan.plan_id
                db.commit()
                user_plan = fetched_plan

        # 🔥 FIX: Calculate credits in real-time from single source of truth
        from models.credit_distribution import CreditDistribution
        from models.message_usage import MessageUsageCreditLog
        from sqlalchemy import func
        
        # Get total credits allocated from credit distributions (single source of truth)
        credits_allocated_db = db.query(func.sum(CreditDistribution.credits_shared)).filter(
            CreditDistribution.to_business_user_id == str(current_user.busi_user_id)
        ).scalar() or 0
        
        # Get total credits used from message usage logs (single source of truth)
        credits_used_db = db.query(func.sum(MessageUsageCreditLog.credits_deducted)).filter(
            MessageUsageCreditLog.busi_user_id == str(current_user.busi_user_id),
            MessageUsageCreditLog.credits_deducted > 0  # Only sum positive deductions
        ).scalar() or 0
        
        # Calculate remaining credits
        credits_remaining_calc = max(0, credits_allocated_db - credits_used_db)

        return {
            "user_type": "business",
            "plan_id": str(current_user.plan_id) if current_user.plan_id else None,
            "plan_name": current_user.plan_name or (user_plan.name if user_plan else "No Active Plan"),
            "plan_expiry": current_user.plan_expiry.isoformat() if current_user.plan_expiry else None,
            "credits_remaining": credits_remaining_calc,
            "credits_allocated": max(0, credits_allocated_db),
            "credits_used": max(0, credits_used_db),
            "whatsapp_mode": current_user.whatsapp_mode or "unofficial",
            "assigned_by_name": assigned_by_name,
            "assigned_by_role": assigned_by_role,
            "is_active": True if user_plan else False,
            "plan": PlanResponseSchema.model_validate(user_plan).model_dump() if user_plan else None
        }
    
    # 2. Handle Resellers
    elif isinstance(current_user, Reseller):
        return {
            "user_type": "reseller",
            "plan_id": str(current_user.plan_id) if current_user.plan_id else None,
            "plan_name": current_user.plan_name or (current_user.plan.name if current_user.plan else "Reseller Portal"),
            "plan_expiry": current_user.plan_expiry.isoformat() if current_user.plan_expiry else None,
            "credits_remaining": current_user.available_credits or 0,
            "credits_allocated": current_user.total_credits or (current_user.plan.credits_offered if current_user.plan else 0),
            "credits_used": current_user.used_credits or 0,
            "whatsapp_mode": "reseller_portal",
            "assigned_by_name": "System",
            "assigned_by_role": "admin",
            "is_active": True if current_user.plan_id else False,
            "plan": PlanResponseSchema.model_validate(current_user.plan).model_dump() if current_user.plan else None
        }
    
    # 3. Handle System Administrators
    elif isinstance(current_user, MasterAdmin):
        return {
            "user_type": "admin",
            "plan_id": "admin-unlimited",
            "plan_name": "System Administrator",
            "plan_expiry": None,
            "credits_remaining": 999999,
            "credits_allocated": 999999,
            "credits_used": 0,
            "whatsapp_mode": "admin",
            "plan": {
                "name": "Super Admin Plan",
                "price": 0,
                "credits_offered": 999999,
                "validity_days": 365,
                "plan_category": "ADMIN"
            }
        }
    
    else:
        raise HTTPException(status_code=403, detail="Invalid user role for plan retrieval")
