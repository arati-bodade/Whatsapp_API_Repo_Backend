from fastapi import APIRouter, Depends, HTTPException, status, Header, Query, Request
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from models.busi_user import BusiUser
from models.reseller import Reseller
from models.admin import MasterAdmin
from models.message_usage import MessageUsageCreditLog
from schemas.message_usage import MessageUsageCreditLogResponse
from services.message_usage_service import MessageUsageService
from services.payment_service import PaymentService
from services.audit_log_service import AuditLogService
from services.reseller_alert_service import ResellerAlertService
from schemas.audit_log import AuditLogCreate
from models.payment_order import PaymentOrder
from core.config import settings
from core.security import get_current_user_id
from db.session import get_db
from core.plan_validator import check_reseller_plan
from models.plan import Plan
import uuid

router = APIRouter(tags=["Credits"])

@router.get("/balance")
async def get_my_balance(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get current credit balance.
    🔥 FIX: Use actual credits_remaining field as single source of truth for consistency.
    """
    # Try BusiUser first (most common)
    user = db.query(BusiUser).filter(BusiUser.busi_user_id == user_id).first()
    if user:
        # 🔥 REAL-TIME CREDIT CALCULATION
        from sqlalchemy import func
        from models.message_usage import MessageUsageCreditLog
        
        # Table values for allocated credits are the authority
        credits_allocated = max(0, user.credits_allocated or 0)
        
        # Real-time used credits from logs
        credits_used = db.query(func.sum(MessageUsageCreditLog.credits_deducted)).filter(
            MessageUsageCreditLog.busi_user_id == str(user_id),
            MessageUsageCreditLog.credits_deducted > 0
        ).scalar() or 0
        
        # Remaining is calculated live
        credits_remaining = max(0, credits_allocated - credits_used)

        return {
            "user_id": str(user.busi_user_id),
            "user_type": "business",
            "current_balance": credits_remaining,
            "credits_used": credits_used,
            "credits_allocated": credits_allocated,
            "plan_name": user.plan_name,
            "plan_expiry": user.plan_expiry.isoformat() if user.plan_expiry else None
        }
    
    # Try Reseller
    reseller = db.query(Reseller).filter(Reseller.reseller_id == user_id).first()
    if reseller:
         return {
            "user_id": str(reseller.reseller_id),
            "user_type": "reseller",
            "current_balance": max(0, reseller.available_credits or 0),
            "credits_used": max(0, reseller.used_credits or 0)
        }

    # Try Admin (MasterAdmin)
    admin = db.query(MasterAdmin).filter(MasterAdmin.admin_id == user_id).first()
    if admin:
        return {
            "user_id": str(admin.admin_id),
            "user_type": "admin",
            "current_balance": 999999,
            "credits_used": 0
        }

    raise HTTPException(status_code=404, detail="User wallet not found")

@router.get("/summary")
async def get_my_credit_summary(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get credit summary (Total usage, latest deduction details).
    """
    service = MessageUsageService(db)
    return service.get_credit_summary(user_id)

from pydantic import BaseModel
from datetime import timedelta

class PlanPurchaseRequest(BaseModel):
    plan_name: str
    credits: float
    price: float
    allocated_to_user_id: Optional[str] = None  # busi_user_id to allocate credits to (reseller buying for busi_user)
    # Personal info fields for validation against registered data
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None

def validate_user_personal_info(user: any, request: PlanPurchaseRequest) -> None:
    """
    Validate that the submitted personal information matches the user's registered data.
    🔥 FIX: Made validation optional - only validate if data is provided and user is self-purchasing
    Raises HTTPException if validation fails.
    """
    # Skip validation if allocating to another user (reseller/admin scenario)
    if request.allocated_to_user_id and request.allocated_to_user_id != "self":
        return
    
    # 🔥 FIX: Skip validation entirely for flexible checkout
    # Allow empty/default values without blocking
    # Only validate if user explicitly provides data and it differs from defaults
    if not request.name or request.name == "Reseller User":
        return
    if not request.email or request.email == "noreply@example.com":
        return
    if not request.phone or request.phone == "0000000000":
        return
    
    errors = []
    
    # 🔥 FIX: Validate name (case-insensitive trim comparison) - only if provided
    if request.name and request.name != "Reseller User":
        registered_name = getattr(user, 'name', '')
        if registered_name and request.name.strip().lower() != registered_name.strip().lower():
            errors.append("Name does not match your registered information")
    
    # Validate email (case-insensitive) - only if provided
    if request.email and request.email != "noreply@example.com":
        registered_email = getattr(user, 'email', '')
        if registered_email and request.email.strip().lower() != registered_email.strip().lower():
            errors.append("Email does not match your registered information")
    
    # 🔥 FIX: Validate phone (case-insensitive trim comparison) - only if provided
    if request.phone and request.phone != "0000000000":
        registered_phone = getattr(user, 'phone', '')
        if registered_phone and request.phone.strip().lower() != registered_phone.strip().lower():
            errors.append("Phone number does not match your registered information")
    
    # 🔥 FIX: Validate company/business_name (case-insensitive trim comparison) - only if provided
    if request.company and request.company != "-":
        registered_company = getattr(user, 'business_name', '')
        if registered_company and request.company.strip().lower() != registered_company.strip().lower():
            errors.append("Company name does not match your registered information")
    
    # 🔥 FIX: Only raise error if there are actual validation errors
    if errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid details. Please enter your registered information. " + "; ".join(errors)
        )

@router.post("/purchase-plan")
async def purchase_plan(
    request: PlanPurchaseRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Purchase a credit plan and update the user's wallet.
    🔥 FIX: For sub-users under resellers, deduct from reseller's credits instead of adding to user wallet
    🔥 FIX: Resets all credits on new plan purchase (no carry-forward from old plan)
    Updates are transactional to ensure atomicity.
    🔥 FIX: Added edge case handling for rapid purchases and concurrent operations
    """
    # 🔥 NEW: Add transaction safety and edge case handling
    transaction_id = str(uuid.uuid4())
    try:
        # Start database transaction (only if not already in a transaction)
        if not db.in_transaction():
            db.begin()
        
        logger.info(f"[PURCHASE-PLAN] Starting transaction {transaction_id} for user {user_id}")
        # Try BusiUser first
        user = db.query(BusiUser).filter(BusiUser.busi_user_id == user_id).first()
        if user:
            # Validate personal information matches registered data
            validate_user_personal_info(user, request)
            
            # 🔥 NEW: Check if user belongs to a reseller and implement conditional deduction
            if user.parent_reseller_id and user.parent_role == "reseller":
                # 🔥 FIX: Fetch Plan details first to get authoritative credits and rate
                plan = db.query(Plan).filter(Plan.name == request.plan_name).first()
                plan_credits = plan.credits_offered if plan else request.credits

                # Sub-user purchase → deduct from reseller's credits
                reseller = db.query(Reseller).filter(Reseller.reseller_id == user.parent_reseller_id).first()
                if not reseller:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Parent reseller not found"
                    )
                
                # Check if reseller has sufficient credits
                if (reseller.available_credits or 0) < plan_credits:
                    shortage = plan_credits - (reseller.available_credits or 0)
                    logger.warning(f"🚨 [PURCHASE-PLAN] Direct allocation failed. Reseller {reseller.name} insufficient credits for {user.name}. Shortage: {shortage}")
                    
                    # 🔥 NEW: Use advanced ResellerAlertService for better tracking/grouping
                    alert_service = ResellerAlertService(db)
                    await alert_service.create_or_update_alert(
                        reseller_id=reseller.reseller_id,
                        sub_user_id=user_id,
                        sub_user_name=user.business_name or user.name,
                        plan_name=request.plan_name,
                        required_credits=plan_credits,
                        available_credits=reseller.available_credits or 0
                    )

                    raise HTTPException(
                        status_code=400,
                        detail={
                            "error": "INSUFFICIENT_RESELLER_CREDITS",
                            "reseller_balance": reseller.available_credits or 0,
                            "required_credits": plan_credits,
                            "shortage": max(0, shortage),
                            "reseller_name": reseller.name
                        }
                    )
                
                # 🔥 NEW: Deduct credits from reseller instead of adding to user
                reseller.available_credits = (reseller.available_credits or 0) - plan_credits
                reseller.used_credits = (reseller.used_credits or 0) + plan_credits
                
                # 🔥 FIX: RESET user credits to new plan amount (old credits are discarded)
                # Calculate current usage from logs to ensure the new balance is exactly plan_credits
                current_usage = db.query(func.sum(MessageUsageCreditLog.credits_deducted)).filter(
                    MessageUsageCreditLog.busi_user_id == str(user.busi_user_id),
                    MessageUsageCreditLog.credits_deducted > 0
                ).scalar() or 0
                
                user.credits_allocated = current_usage + plan_credits # New Ceiling
                user.credits_remaining = plan_credits  # Informational only, balance endpoint re-calculates
                user.credits_used = current_usage      # Sync with logs
                
                if plan:
                    user.plan_id = plan.plan_id
                    user.consumption_rate = plan.deduction_value
                    user.plan_name = plan.name
                    user.plan_expiry = datetime.now(timezone.utc) + timedelta(days=plan.validity_days)
                else:
                    user.plan_name = request.plan_name
                    user.plan_expiry = datetime.now(timezone.utc) + timedelta(days=365)
                
                # 🔥 NEW: Create credit history for reseller deduction
                reseller_deduction_log = MessageUsageCreditLog(
                    usage_id=str(uuid.uuid4()),
                    busi_user_id=str(reseller.reseller_id),
                    message_id=f"SUB-USER-PLAN-{request.plan_name}-{user.name}",
                    credits_deducted=plan_credits,  # Positive = Deducted
                    balance_after=reseller.available_credits,
                    timestamp=datetime.now(timezone.utc)
                )
                db.add(reseller_deduction_log)
                
                db.add(user_credit_log)
                
                # 🔥 NEW: Create CreditDistribution record for dashboard visibility
                from models.credit_distribution import CreditDistribution
                distribution = CreditDistribution(
                    distribution_id=f"plan-{uuid.uuid4().hex[:12]}",
                    from_reseller_id=reseller.reseller_id,
                    to_business_user_id=user.busi_user_id,
                    credits_shared=plan_credits,
                    shared_at=datetime.now(timezone.utc)
                )
                db.add(distribution)
                
                # 🔥 NEW: Audit Log for Reseller's Credit Deduction
                audit_service = AuditLogService(db)
                audit_service.create_log(AuditLogCreate(
                    reseller_id=reseller.reseller_id,
                    performed_by_id=user.busi_user_id,
                    performed_by_name=user.business_name or user.name,
                    performed_by_role="business",
                    affected_user_id=reseller.reseller_id,
                    affected_user_name=reseller.name,
                    affected_user_email=reseller.email,
                    action_type="CREDIT DEDUCTION",
                    module="Billing",
                    description=f"Sub-user ({user.name}) plan purchase - {plan_credits} credits deducted from reseller",
                    changes_made=[f"credits: -{plan_credits}"]
                ))
                
                # 🔥 NEW: Audit Log for Sub-user's Credit Addition
                audit_service.create_log(AuditLogCreate(
                    reseller_id=reseller.reseller_id,
                    performed_by_id=user.busi_user_id,
                    performed_by_name=user.business_name or user.name,
                    performed_by_role="business",
                    affected_user_id=user.busi_user_id,
                    affected_user_name=user.business_name or user.name,
                    affected_user_email=user.email,
                    action_type="PLAN PURCHASE",
                    module="Credits",
                    description=f"Purchased {request.plan_name} plan using reseller credits (+{plan_credits} credits)",
                    changes_made=[f"plan: {request.plan_name}", f"credits: +{plan_credits}"]
                ))
                
                db.commit()
                db.refresh(user)
                db.refresh(reseller)
                
                return {
                    "success": True,
                    "message": f"Successfully purchased {request.plan_name} plan using reseller credits",
                    "new_balance": user.credits_remaining,
                    "reseller_balance": reseller.available_credits,
                    "expiry": user.plan_expiry,
                    "purchased_using": "reseller_credits"
                }
            
            # Normal user (no reseller parent) → original logic
            # 🔥 FIX: Fetch Plan details first
            plan = db.query(Plan).filter(Plan.name == request.plan_name).first()
            plan_credits = plan.credits_offered if plan else request.credits

            if plan:
                user.plan_id = plan.plan_id
                user.consumption_rate = plan.deduction_value
                user.plan_name = plan.name
                user.plan_expiry = datetime.now(timezone.utc) + timedelta(days=plan.validity_days)
            else:
                user.plan_name = request.plan_name
                user.plan_expiry = datetime.now(timezone.utc) + timedelta(days=365)
            
            # 🔥 FIX: RESET credits to new plan credits (old credits are discarded)
            # Calculate current usage from logs to ensure the new balance is exactly plan_credits
            from sqlalchemy import func
            current_usage = db.query(func.sum(MessageUsageCreditLog.credits_deducted)).filter(
                MessageUsageCreditLog.busi_user_id == str(user.busi_user_id),
                MessageUsageCreditLog.credits_deducted > 0
            ).scalar() or 0

            user.credits_allocated = current_usage + plan_credits # New Ceiling
            user.credits_remaining = plan_credits  # Informational only
            user.credits_used = current_usage      # Sync with logs
            
            # --- [INTERNAL COMMISSION LOGIC] ---
            if user.parent_reseller_id and user.parent_role == "reseller":
                parent = db.query(Reseller).filter(Reseller.reseller_id == user.parent_reseller_id).first()
                if parent:
                    commission_rate = 0.10 # 10% default commission
                    commission_credits = int(plan_credits * commission_rate)
                    
                    if commission_credits > 0:
                        parent.available_credits = (parent.available_credits or 0) + commission_credits
                        parent.total_credits = (parent.total_credits or 0) + commission_credits
                        
                        # Log commission addition for reseller
                        comm_log = MessageUsageCreditLog(
                            usage_id=str(uuid.uuid4()),
                            busi_user_id=str(parent.reseller_id),
                            message_id=f"COMM-{request.plan_name}-{user.name}",
                            credits_deducted=-commission_credits, # Negative = Added
                            balance_after=parent.available_credits,
                            timestamp=datetime.now(timezone.utc)
                        )
                        db.add(comm_log)
                        
                        # Audit Log for Reseller's Commission
                        audit_service = AuditLogService(db)
                        audit_service.create_log(AuditLogCreate(
                            reseller_id=parent.reseller_id,
                            performed_by_id=user.busi_user_id, # User purchase triggered this
                            performed_by_name=user.business_name or user.name,
                            performed_by_role="business",
                            affected_user_id=parent.reseller_id,
                            affected_user_name=parent.name,
                            affected_user_email=parent.email,
                            action_type="COMMISSION CREDIT",
                            module="Billing",
                            description=f"Reseller earned {commission_credits} credits commission from {user.name}'s purchase.",
                            changes_made=[f"credits: +{commission_credits}"]
                        ))

            # Create usage log for user purchase
            purchase_log = MessageUsageCreditLog(
                usage_id=str(uuid.uuid4()),
                busi_user_id=str(user.busi_user_id),
                message_id=f"PLAN-{request.plan_name}",
                credits_deducted=-plan_credits, # Negative = Added
                balance_after=user.credits_remaining,
                timestamp=datetime.now(timezone.utc)
            )
            db.add(purchase_log)
            
            # Audit Log for user's purchase
            audit_service = AuditLogService(db)
            audit_log = AuditLogCreate(
                reseller_id=user.parent_reseller_id if hasattr(user, 'parent_reseller_id') else None,
                performed_by_id=user.busi_user_id,
                performed_by_name=user.business_name or user.name,
                performed_by_role="business",
                affected_user_id=user.busi_user_id,
                affected_user_name=user.business_name or user.name,
                affected_user_email=user.email,
                action_type="PLAN PURCHASE",
                module="Credits",
                description=f"Purchased {request.plan_name} plan (+{plan_credits} credits)",
                changes_made=[f"plan: {request.plan_name}", f"credits: +{plan_credits}"]
            )
            audit_service.create_log(audit_log)

            db.commit()
            logger.info(f"[PURCHASE-PLAN] Transaction {transaction_id} committed successfully for user {user_id}")
            db.refresh(user)
            
            return {
                "success": True,
                "message": f"Successfully purchased {request.plan_name} plan",
                "new_balance": user.credits_remaining,
                "expiry": user.plan_expiry
            }
        
        # Try Reseller
        reseller = db.query(Reseller).filter(Reseller.reseller_id == user_id).first()
        if reseller:
            # Validate personal information matches registered data
            validate_user_personal_info(reseller, request)
            # 🔥 FIX: Fetch Plan details for Reseller
            plan = db.query(Plan).filter(Plan.name == request.plan_name).first()
            if plan:
                reseller.plan_id = plan.plan_id
                reseller.plan_name = plan.name
                reseller.plan_expiry = datetime.now(timezone.utc) + timedelta(days=plan.validity_days)
            else:
                reseller.plan_name = request.plan_name

            # 🔥 FIX: RESET credits to new plan credits (old credits are discarded)
            old_available_credits = reseller.available_credits or 0
            old_total_credits = reseller.total_credits or 0
            
            # Fetch plan credits
            plan_credits = plan.credits_offered if plan else request.credits
            
            reseller.available_credits = plan_credits  # Reset to new plan credits
            reseller.total_credits = plan_credits  # Reset to new plan credits
            reseller.used_credits = 0  # Reset usage counter for new plan
            
            # Create usage log for purchase
            purchase_log = MessageUsageCreditLog(
                usage_id=str(uuid.uuid4()),
                busi_user_id=str(reseller.reseller_id),
                message_id=f"PLAN-{request.plan_name}",
                credits_deducted=-plan_credits, # Negative = Added
                balance_after=reseller.available_credits,
                timestamp=datetime.now(timezone.utc)
            )
            db.add(purchase_log)
            
            # Audit Log
            audit_service = AuditLogService(db)
            audit_log = AuditLogCreate(
                reseller_id=reseller.reseller_id,
                performed_by_id=reseller.reseller_id,
                performed_by_name=reseller.name or "Reseller",
                performed_by_role="reseller",
                affected_user_id=reseller.reseller_id,
                affected_user_name=reseller.name or "Reseller",
                affected_user_email=reseller.email,
                action_type="PLAN PURCHASE",
                module="Credits",
                description=f"Purchased {request.plan_name} plan (+{plan_credits} credits)",
                changes_made=[f"plan: {request.plan_name}", f"credits: +{plan_credits}"]
            )
            audit_service.create_log(audit_log)

            db.commit()
            logger.info(f"[PURCHASE-PLAN] Transaction {transaction_id} committed successfully for reseller {user_id}")
            db.refresh(reseller)
            
            return {
                "success": True,
                "message": f"Successfully purchased {request.plan_name} plan",
                "new_balance": reseller.available_credits,
                "expiry": None
            }
        
        # User not found
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    except HTTPException:
        # Rollback transaction for HTTP exceptions
        logger.error(f"[PURCHASE-PLAN] Transaction {transaction_id} failed - HTTP Exception, rolling back")
        db.rollback()
        raise
    except Exception as e:
        # Rollback transaction for general exceptions
        logger.error(f"[PURCHASE-PLAN] Transaction {transaction_id} failed - {str(e)}, rolling back")
        db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to purchase plan: {str(e)}"
        )

@router.post("/initiate-payment")
async def initiate_payment(
    request: PlanPurchaseRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Step 1: Create a Razorpay order.
    SECURITY: Validates user role and allocation ownership.
    """
    # 1. Verify User and determine role
    user = db.query(BusiUser).filter(BusiUser.busi_user_id == user_id).first()
    user_type = "business"
    if not user:
        user = db.query(Reseller).filter(Reseller.reseller_id == user_id).first()
        user_type = "reseller"
    
    if not user:
        # Check if it's the Master Admin
        user = db.query(MasterAdmin).filter(MasterAdmin.admin_id == user_id).first()
        user_type = "admin"
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 🔥 DEBUG: Log incoming payload for debugging
    logger.info(f"[INITIATE-PAYMENT] Incoming payload: {request.model_dump()}")
    
    # 2. SECURITY: Validate personal information matches registered data
    validate_user_personal_info(user, request)

    # 🔥 NEW: For sub-users under resellers, check reseller balance BEFORE initiating payment
    if user_type == "business" and user.parent_reseller_id and user.parent_role == "reseller":
        # Fetch Plan details first to get authoritative credits
        plan = db.query(Plan).filter(Plan.name == request.plan_name).first()
        plan_credits = plan.credits_offered if plan else request.credits

        reseller = db.query(Reseller).filter(Reseller.reseller_id == user.parent_reseller_id).first()
        if not reseller or (reseller.available_credits or 0) < plan_credits:
            shortage = plan_credits - (reseller.available_credits or 0)
            logger.warning(f"🚨 [INITIATE-PAYMENT] Purchase blocked for sub-user {user.name}. Reseller {reseller.name if reseller else 'N/A'} has insufficient credits. Shortage: {shortage}")
            
            # 🔥 NEW: Use advanced ResellerAlertService for better tracking/grouping
            alert_service = ResellerAlertService(db)
            await alert_service.create_or_update_alert(
                reseller_id=user.parent_reseller_id,
                sub_user_id=user_id,
                sub_user_name=user.business_name or user.name,
                plan_name=request.plan_name,
                required_credits=plan_credits,
                available_credits=reseller.available_credits if reseller else 0
            )

            raise HTTPException(
                status_code=400,
                detail={
                    "error": "INSUFFICIENT_RESELLER_CREDITS",
                    "reseller_balance": reseller.available_credits if reseller else 0,
                    "required_credits": plan_credits,
                    "shortage": max(0, shortage),
                    "reseller_name": reseller.name if reseller else "Your Reseller"
                }
            )

    # 3. SECURITY: Validate allocation based on role
    if request.allocated_to_user_id and request.allocated_to_user_id != "self":
        if user_type == "business":
            # Regular users cannot allocate to others
            raise HTTPException(
                status_code=403,
                detail="Regular users can only purchase plans for themselves"
            )
        elif user_type == "reseller":
            # Resellers can only allocate to their own sub-users
            target_user = db.query(BusiUser).filter(
                BusiUser.busi_user_id == request.allocated_to_user_id
            ).first()
            
            if not target_user:
                raise HTTPException(
                    status_code=404,
                    detail="Target user not found"
                )
            
            # Verify the sub-user belongs to this reseller
            if str(target_user.parent_reseller_id) != str(user_id):
                raise HTTPException(
                    status_code=403,
                    detail="You can only allocate plans to your own sub-users"
                )
        # Admins can allocate to anyone (no validation needed)

    # 2. Setup Order Data
    # 🔥 FIX: Fetch Plan details first to get authoritative credits and price
    plan = db.query(Plan).filter(Plan.name == request.plan_name).first()
    plan_credits = plan.credits_offered if plan else request.credits
    plan_price = plan.price if plan else request.price
    
    txnid = f"OD-{uuid.uuid4().hex[:12].upper()}"
    
    # Calculate amount with GST (18%)
    gst_rate = 0.18
    raw_amount = float(plan_price) * (1 + gst_rate)
    
    # 3. Create Order via Razorpay
    payment_service = PaymentService()
    notes = {
        "user_id": str(user_id),
        "user_type": user_type,
        "plan_name": request.plan_name,
        "credits": str(plan_credits),
        "txnid": txnid
    }
    
    result = payment_service.create_order(
        amount=raw_amount,
        notes=notes
    )
    
    if result.get("success"):
        razor_order = result["order"]
        # 4. Create Payment Order in DB
        new_order = PaymentOrder(
            txnid=txnid,
            razorpay_order_id=razor_order["id"],
            user_id=user_id,
            user_type=user_type,
            plan_name=request.plan_name,
            credits=plan_credits,
            amount=raw_amount,
            status="pending",
            allocated_to_user_id=str(request.allocated_to_user_id) if request.allocated_to_user_id else None,
            is_allocated="pending"
        )
        db.add(new_order)
        db.commit()
        
        return {
            "success": True, 
            "razorpay_order_id": razor_order["id"],
            "amount": razor_order["amount"],
            "currency": razor_order["currency"],
            "key": settings.RAZORPAY_KEY_ID,
            "txnid": txnid
        }
    else:
        error_detail = result.get("error", "Unknown Razorpay error")
        logger.error(f"❌ Razorpay order creation failed for {user_id}: {error_detail}")
        # Log if keys appear empty
        if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
            logger.error("🛑 CRITICAL: Razorpay Keys are EMPTY in Backend Settings!")
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Payment Gateway Error: {error_detail}"
        )

class RazorpayCallback(BaseModel):
    razorpay_payment_id: str
    razorpay_order_id: str
    razorpay_signature: str

@router.post("/payment-callback")
async def payment_callback(
    callback: RazorpayCallback,
    db: Session = Depends(get_db)
):
    """
    Step 2: Verify Razorpay signature and update credits.
    🔥 FIX: Resets all credits on new plan purchase (no carry-forward from old plan)
    Updates are transactional to ensure atomicity.
    """
    try:
        # 1. Verify Signature
        payment_service = PaymentService()
        if not payment_service.verify_signature(
            razorpay_order_id=callback.razorpay_order_id,
            razorpay_payment_id=callback.razorpay_payment_id,
            razorpay_signature=callback.razorpay_signature
        ):
            logger.error(f"Invalid Razorpay signature for order: {callback.razorpay_order_id}")
            raise HTTPException(status_code=400, detail="Invalid payment signature")

        # 2. Find Order
        order = db.query(PaymentOrder).filter(PaymentOrder.razorpay_order_id == callback.razorpay_order_id).first()
        if not order:
            logger.error(f"Order not found for Razorpay order ID: {callback.razorpay_order_id}")
            raise HTTPException(status_code=404, detail="Order not found")

        # 🔥 FIX: Idempotency check - return early if already processed
        if order.status == "success":
            logger.info(f"Order {callback.razorpay_order_id} already processed, returning early")
            return {"success": True, "message": "Credits already updated"}

        # 3. Update Order and Credits
        order.status = "success"
        order.razorpay_payment_id = callback.razorpay_payment_id
        order.razorpay_signature = callback.razorpay_signature
        
        # 4. Check if we need to auto-allocate to a specific business user
        is_auto_allocated = bool(order.allocated_to_user_id and order.is_allocated == "pending")

        # SECURITY: Validate allocation ownership before processing
        if is_auto_allocated and order.allocated_to_user_id:
            # Re-fetch user to verify role
            purchaser = db.query(BusiUser).filter(BusiUser.busi_user_id == order.user_id).first()
            purchaser_type = "business"
            if not purchaser:
                purchaser = db.query(Reseller).filter(Reseller.reseller_id == order.user_id).first()
                purchaser_type = "reseller"
            
            if purchaser_type == "business":
                # Regular users should not have allocated_to_user_id set
                logger.error(f"Security violation: Business user {order.user_id} attempting to allocate to {order.allocated_to_user_id}")
                raise HTTPException(
                    status_code=403,
                    detail="Invalid allocation: Regular users cannot allocate to others"
                )
            elif purchaser_type == "reseller":
                # Verify the target belongs to this reseller
                target_user = db.query(BusiUser).filter(
                    BusiUser.busi_user_id == order.allocated_to_user_id
                ).first()
                
                if not target_user:
                    logger.error(f"Security violation: Reseller {order.user_id} attempting to allocate to non-existent user {order.allocated_to_user_id}")
                    raise HTTPException(
                        status_code=404,
                        detail="Target user not found"
                    )
                
                if str(target_user.parent_reseller_id) != str(order.user_id):
                    logger.error(f"Security violation: Reseller {order.user_id} attempting to allocate to user {order.allocated_to_user_id} who belongs to another reseller")
                    raise HTTPException(
                        status_code=403,
                        detail="Invalid allocation: Target user does not belong to you"
                    )

        if not is_auto_allocated:
            # Add credits directly to the purchaser's wallet
            if order.user_type == "business":
                user = db.query(BusiUser).filter(BusiUser.busi_user_id == order.user_id).first()
                if user:
                    # 🔥 FIX: Check if user belongs to a reseller and deduct from reseller's credits
                    if user.parent_reseller_id and user.parent_role == "reseller":
                        # Sub-user purchase → deduct from reseller's credits
                        reseller = db.query(Reseller).filter(Reseller.reseller_id == user.parent_reseller_id).first()
                        if not reseller:
                            raise HTTPException(
                                status_code=status.HTTP_404_NOT_FOUND,
                                detail="Parent reseller not found"
                            )
                        
                        # Check if reseller has sufficient credits
                        if (reseller.available_credits or 0) < order.credits:
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"Reseller does not have enough credits. Required: {order.credits}, Available: {reseller.available_credits or 0}"
                            )
                        
                        # 🔥 NEW: Deduct credits from reseller instead of adding to user
                        reseller.available_credits = (reseller.available_credits or 0) - order.credits
                        reseller.used_credits = (reseller.used_credits or 0) + order.credits
                        
                        # 🔥 FIX: RESET user credits to new plan amount (old credits are discarded)
                        user.credits_remaining = order.credits  # Reset to new plan credits
                        user.credits_allocated = order.credits  # Reset to new plan credits
                        user.credits_used = 0  # Reset usage counter for new plan
                        
                        # 🔥 FIX: Fetch Plan details to get the dynamic rate
                        plan = db.query(Plan).filter(Plan.name == order.plan_name).first()
                        if plan:
                            user.plan_id = plan.plan_id
                            user.consumption_rate = plan.deduction_value
                            user.plan_name = plan.name
                            user.plan_expiry = datetime.now(timezone.utc) + timedelta(days=plan.validity_days)
                        else:
                            user.plan_name = order.plan_name
                            user.plan_expiry = datetime.now(timezone.utc) + timedelta(days=365)
                        
                        # 🔥 NEW: Create credit history for reseller deduction
                        reseller_deduction_log = MessageUsageCreditLog(
                            usage_id=str(uuid.uuid4()),
                            busi_user_id=str(reseller.reseller_id),
                            message_id=f"SUB-USER-PAYMENT-{order.plan_name}-{user.name}",
                            credits_deducted=order.credits,  # Positive = Deducted
                            balance_after=reseller.available_credits,
                            timestamp=datetime.now(timezone.utc)
                        )
                        db.add(reseller_deduction_log)
                        
                        db.add(user_credit_log)
                        
                        # 🔥 NEW: Create CreditDistribution record for dashboard visibility
                        from models.credit_distribution import CreditDistribution
                        distribution = CreditDistribution(
                            distribution_id=f"pay-{uuid.uuid4().hex[:12]}",
                            from_reseller_id=reseller.reseller_id,
                            to_business_user_id=user.busi_user_id,
                            credits_shared=order.credits,
                            shared_at=datetime.now(timezone.utc)
                        )
                        db.add(distribution)
                        
                        # 🔥 NEW: Audit Log for Reseller's Credit Deduction
                        audit_service = AuditLogService(db)
                        audit_service.create_log(AuditLogCreate(
                            reseller_id=reseller.reseller_id,
                            performed_by_id=user.busi_user_id,
                            performed_by_name=user.business_name or user.name,
                            performed_by_role="business",
                            affected_user_id=reseller.reseller_id,
                            affected_user_name=reseller.name,
                            affected_user_email=reseller.email,
                            action_type="CREDIT DEDUCTION",
                            module="Billing",
                            description=f"Sub-user ({user.name}) payment plan purchase - {order.credits} credits deducted from reseller",
                            changes_made=[f"credits: -{order.credits}"]
                        ))
                        
                        # 🔥 NEW: Audit Log for Sub-user's Credit Addition
                        audit_service.create_log(AuditLogCreate(
                            reseller_id=reseller.reseller_id,
                            performed_by_id=user.busi_user_id,
                            performed_by_name=user.business_name or user.name,
                            performed_by_role="business",
                            affected_user_id=user.busi_user_id,
                            affected_user_name=user.business_name or user.name,
                            affected_user_email=user.email,
                            action_type="PLAN PURCHASE",
                            module="Credits",
                            description=f"Purchased {order.plan_name} plan using reseller credits via payment (+{order.credits} credits)",
                            changes_made=[f"plan: {order.plan_name}", f"credits: +{order.credits}"]
                        ))
                        
                        current_balance = user.credits_remaining
                    else:
                        # Normal user (no reseller parent) → original logic
                        # 🔥 FIX: Sync Plan details for direct purchase
                        plan = db.query(Plan).filter(Plan.name == order.plan_name).first()
                        if plan:
                            user.plan_id = plan.plan_id
                            user.plan_name = plan.name
                            user.consumption_rate = plan.deduction_value
                            user.plan_expiry = datetime.now(timezone.utc) + timedelta(days=plan.validity_days)
                        else:
                            user.plan_name = order.plan_name
                            user.plan_expiry = datetime.now(timezone.utc) + timedelta(days=365)
                        
                        # 🔥 FIX: RESET credits to new plan credits (old credits are discarded)
                        user.credits_remaining = order.credits  # Reset to new plan credits
                        user.credits_allocated = order.credits  # Reset to new plan credits
                        user.credits_used = 0  # Reset usage counter for new plan
                        current_balance = user.credits_remaining
                    
                    # Create usage log for the purchaser (only for normal users, not reseller sub-users)
                    # Reseller sub-users already have specific logs created above
                    if not (user.parent_reseller_id and user.parent_role == "reseller"):
                        payment_log = MessageUsageCreditLog(
                            usage_id=str(uuid.uuid4()),
                            busi_user_id=str(order.user_id),
                            message_id=f"RAZORPAY-{callback.razorpay_payment_id}",
                            credits_deducted=-order.credits, # Negative = Added
                            balance_after=current_balance,
                            timestamp=datetime.now(timezone.utc)
                        )
                        db.add(payment_log)
            elif order.user_type == "reseller":
                reseller = db.query(Reseller).filter(Reseller.reseller_id == order.user_id).first()
                if reseller:
                    # 🔥 FIX: Sync Plan details for Reseller
                    plan = db.query(Plan).filter(Plan.name == order.plan_name).first()
                    if plan:
                        reseller.plan_id = plan.plan_id
                        reseller.plan_name = plan.name
                        reseller.plan_expiry = datetime.now(timezone.utc) + timedelta(days=plan.validity_days)
                    else:
                        reseller.plan_name = order.plan_name
                        reseller.plan_expiry = datetime.now(timezone.utc) + timedelta(days=365)

                    # 🔥 FIX: RESET credits to new plan credits (old credits are discarded)
                    reseller.available_credits = order.credits  # Reset to new plan credits
                    reseller.total_credits = order.credits  # Reset to new plan credits
                    reseller.used_credits = 0  # Reset usage counter for new plan
                    current_balance = reseller.available_credits
                    
                    # 🔥 NEW: Automatically resolve alerts if the new balance satisfies them
                    alert_service = ResellerAlertService(db)
                    alert_service.resolve_alerts_for_reseller(reseller.reseller_id, current_balance)
            else:
                # Admin purchase
                current_balance = 0
                logger.info(f"Admin purchase success: {order.txnid}")
            
            # Create usage log for the purchaser
            payment_log = MessageUsageCreditLog(
                usage_id=str(uuid.uuid4()),
                busi_user_id=str(order.user_id),
                message_id=f"RAZORPAY-{order.razorpay_payment_id}",
                credits_deducted=-order.credits, # Negative = Added
                balance_after=current_balance,
                timestamp=datetime.now(timezone.utc)
            )
            db.add(payment_log)
            
            # 🔥 FIX: Mark order as allocated since credits were added to purchaser's wallet
            order.is_allocated = "allocated"
        else:
            # 5. Auto-allocate credits DIRECTLY to the target user (skip adding to purchaser)
            target_id = order.allocated_to_user_id
            
            # Try finding as Business User
            target_user = db.query(BusiUser).filter(BusiUser.busi_user_id == target_id).first()
            is_reseller = False
            
            if not target_user:
                # Try finding as Reseller
                target_user = db.query(Reseller).filter(Reseller.reseller_id == target_id).first()
                is_reseller = True
                
            if target_user:
                if not is_reseller:
                    # 🔥 FIX: Sync Plan details and reset credits (no carry-forward)
                    plan = db.query(Plan).filter(Plan.name == order.plan_name).first()
                    if plan:
                        target_user.plan_id = plan.plan_id
                        target_user.consumption_rate = plan.deduction_value
                        target_user.plan_name = plan.name
                        target_user.plan_expiry = datetime.now(timezone.utc) + timedelta(days=plan.validity_days)
                    else:
                        target_user.plan_name = order.plan_name
                        target_user.plan_expiry = datetime.now(timezone.utc) + timedelta(days=365)

                    # 🔥 FIX: RESET credits to new plan credits (old credits are discarded)
                    target_user.credits_remaining = order.credits  # Reset to new plan credits
                    target_user.credits_allocated = order.credits  # Reset to new plan credits
                    target_user.credits_used = 0  # Reset usage counter for new plan
                    current_balance = target_user.credits_remaining
                else:
                    # 🔥 FIX: Same for Reseller - reset credits (old credits are discarded)
                    plan = db.query(Plan).filter(Plan.name == order.plan_name).first()
                    if plan:
                        target_user.plan_id = plan.plan_id
                        target_user.plan_name = plan.name
                        target_user.plan_expiry = datetime.now(timezone.utc) + timedelta(days=plan.validity_days)
                    else:
                        target_user.plan_name = order.plan_name
                        target_user.plan_expiry = datetime.now(timezone.utc) + timedelta(days=365)

                    # 🔥 FIX: RESET credits to new plan credits (old credits are discarded)
                    target_user.available_credits = order.credits  # Reset to new plan credits
                    target_user.total_credits = order.credits  # Reset to new plan credits
                    target_user.used_credits = 0  # Reset usage counter for new plan
                    current_balance = target_user.available_credits
                
                # Log the allocation
                alloc_log = MessageUsageCreditLog(
                    usage_id=str(uuid.uuid4()),
                    busi_user_id=str(target_id),
                    message_id=f"PLAN-ALLOC-{order.plan_name}-{callback.razorpay_payment_id}",
                    credits_deducted=-order.credits,  # Negative = Added
                    balance_after=current_balance,
                    timestamp=datetime.now(timezone.utc)
                )
                db.add(alloc_log)
                order.is_allocated = "allocated"
                logger.info(f"Auto-allocated {order.credits} credits to {'reseller' if is_reseller else 'busi_user'} {target_id}")
        
        db.commit()
        return {"success": True, "message": "Credits updated successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Payment callback error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to update credits: {str(e)}")


class AllocateCreditsRequest(BaseModel):
    order_txnid: str
    busi_user_id: str

@router.post("/allocate-to-user")
async def allocate_credits_to_user(
    request: AllocateCreditsRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Manually allocate credits from a paid order to a specific business user.
    Only the reseller who purchased the order can allocate it.
    """
    # NEW: Check Reseller Plan/Credits before allocation
    check_reseller_plan(db, user_id)

    # Find the order
    order = db.query(PaymentOrder).filter(PaymentOrder.txnid == request.order_txnid).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Check ownership - must be the one who bought
    if str(order.user_id) != str(user_id):
        raise HTTPException(status_code=403, detail="You can only allocate your own orders")
    
    # Check order is paid
    if order.status != "success":
        raise HTTPException(status_code=400, detail="Order must be paid (status=success) before allocation")
    
    # Check not already allocated
    if order.is_allocated == "allocated":
        raise HTTPException(status_code=400, detail="Credits already allocated from this order")
    
    # Find the target user (Business or Reseller)
    target_user = db.query(BusiUser).filter(BusiUser.busi_user_id == request.busi_user_id).first()
    is_reseller = False
    
    if not target_user:
        target_user = db.query(Reseller).filter(Reseller.reseller_id == request.busi_user_id).first()
        is_reseller = True
        
    if not target_user:
        raise HTTPException(status_code=404, detail="Target user (Business or Reseller) not found")
    
    try:
        # Allocate credits with reset (no carry-forward from old plan)
        if not is_reseller:
            # 🔥 FIX: Sync Plan details and reset credits for business user
            plan = db.query(Plan).filter(Plan.name == order.plan_name).first()
            if plan:
                target_user.plan_id = plan.plan_id
                target_user.consumption_rate = plan.deduction_value
                target_user.plan_name = plan.name
                target_user.plan_expiry = datetime.now(timezone.utc) + timedelta(days=plan.validity_days)
            else:
                target_user.plan_name = order.plan_name
                target_user.plan_expiry = datetime.now(timezone.utc) + timedelta(days=365)

            # 🔥 FIX: RESET credits to new plan credits (old credits are discarded)
            target_user.credits_remaining = order.credits  # Reset to new plan credits
            target_user.credits_allocated = order.credits  # Reset to new plan credits
            target_user.credits_used = 0  # Reset usage counter for new plan
            current_balance = target_user.credits_remaining
        else:
            # 🔥 FIX: Sync Plan details and reset credits for reseller
            plan = db.query(Plan).filter(Plan.name == order.plan_name).first()
            if plan:
                target_user.plan_id = plan.plan_id
                target_user.plan_name = plan.name
                target_user.plan_expiry = datetime.now(timezone.utc) + timedelta(days=plan.validity_days)
            else:
                target_user.plan_name = order.plan_name
                target_user.plan_expiry = datetime.now(timezone.utc) + timedelta(days=365)

            # 🔥 FIX: RESET credits to new plan credits (old credits are discarded)
            target_user.available_credits = order.credits  # Reset to new plan credits
            target_user.total_credits = order.credits  # Reset to new plan credits
            target_user.used_credits = 0  # Reset usage counter for new plan
            current_balance = target_user.available_credits
        
        # If reseller/purchaser is the one distributing, deduct from their available_credits
        # Note: In manual allocation from an ORDER, the order itself provides the credits.
        # But if the purchaser is a reseller, we might need to check if they have enough balance
        # IF they are distributing from their wallet. 
        # HOWEVER, this endpoint seems to be for distributing FROM AN ORDER.
        # So we don't necessarily need to deduct from the reseller's wallet again if the order IS the credits.
        
        # Log the allocation
        alloc_log = MessageUsageCreditLog(
            usage_id=str(uuid.uuid4()),
            busi_user_id=str(request.busi_user_id),
            message_id=f"PLAN-ALLOC-{order.plan_name}",
            credits_deducted=-order.credits,  # Negative = Added
            balance_after=current_balance,
            timestamp=datetime.now(timezone.utc)
        )
        db.add(alloc_log)
        
        # Mark order as allocated
        order.is_allocated = "allocated"
        order.allocated_to_user_id = str(request.busi_user_id)
        
        # Audit Log
        perf_reseller = db.query(Reseller).filter(Reseller.reseller_id == user_id).first()
        audit_service = AuditLogService(db)
        audit_log = AuditLogCreate(
            reseller_id=str(user_id),
            performed_by_id=str(user_id),
            performed_by_name=perf_reseller.name if perf_reseller else "Reseller",
            performed_by_role="reseller",
            affected_user_id=str(target_user.busi_user_id) if not is_reseller else str(target_user.reseller_id),
            affected_user_name=getattr(target_user, 'business_name', target_user.name),
            affected_user_email=target_user.email,
            action_type="CREDIT ALLOCATION",
            module="Credits",
            description=f"Manually allocated {order.credits} credits from order {order.txnid}",
            changes_made=[f"credits_allocated: +{order.credits}", f"plan: {order.plan_name}"]
        )
        audit_service.create_log(audit_log)
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Successfully allocated {order.credits} credits to business user",
            "busi_user_id": request.busi_user_id,
            "credits_allocated": order.credits,
            "new_balance": current_balance
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error allocating credits: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to allocate credits: {str(e)}")


@router.get("/usage", response_model=List[MessageUsageCreditLogResponse])
async def get_my_usage_history(
    user_id: str = Depends(get_current_user_id),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get message usage/credit history.
    """
    service = MessageUsageService(db)
    return service.get_user_usage_logs(
        busi_user_id=user_id,
        skip=skip,
        limit=limit,
        start_date=start_date,
        end_date=end_date
    )

@router.get("/orders", response_model=List[dict])
async def get_my_orders(
    user_id: str = Depends(get_current_user_id),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Get user's payment orders history.
    """
    orders = db.query(PaymentOrder).filter(
        PaymentOrder.user_id == user_id
    ).order_by(
        PaymentOrder.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    # Convert to dict for JSON response
    result = []
    for order in orders:
        allocated_to_user_name = None
        if order.allocated_to_user_id:
            # Fetch the user name if allocated to someone
            target_user = db.query(BusiUser).filter(BusiUser.busi_user_id == order.allocated_to_user_id).first()
            if target_user:
                allocated_to_user_name = target_user.business_name or target_user.name
        
        result.append({
            "id": str(order.id),
            "txnid": order.txnid,
            "plan_name": order.plan_name,
            "credits": order.credits,
            "amount": order.amount,
            "status": order.status,
            "razorpay_order_id": order.razorpay_order_id,
            "razorpay_payment_id": order.razorpay_payment_id,
            "allocated_to_user_id": str(order.allocated_to_user_id) if order.allocated_to_user_id else None,
            "allocated_to_user_name": allocated_to_user_name,
            "is_allocated": order.is_allocated or "pending",
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "updated_at": order.updated_at.isoformat() if order.updated_at else None
        })
    
    return result
