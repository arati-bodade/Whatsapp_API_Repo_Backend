from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from typing import List, Optional, Tuple
from datetime import datetime, timezone
import uuid

from models.message_usage import MessageUsageCreditLog
from models.reseller import Reseller
from models.busi_user import BusiUser
from models.plan import Plan
from schemas.message_usage import (
    MessageUsageCreditLogCreate,
    MessageUsageCreditLogUpdate
)


class MessageUsageService:
    def __init__(self, db: Session):
        self.db = db

    def create_usage_log(self, usage_data: MessageUsageCreditLogCreate) -> MessageUsageCreditLog:
        """Create a new message usage credit log entry."""
        # Auto-generate usage_id
        generated_usage_id = uuid.uuid4()
        
        # Detect user type (reseller or business)
        user_type = self.get_user_type(usage_data.busi_user_id)
        
        db_usage = MessageUsageCreditLog(
            usage_id=generated_usage_id,
            busi_user_id=usage_data.busi_user_id,
            message_id=usage_data.message_id,
            credits_deducted=usage_data.credits_deducted,
            balance_after=usage_data.balance_after,
            timestamp=usage_data.timestamp or datetime.now(timezone.utc)
        )
        
        self.db.add(db_usage)
        self.db.commit()
        self.db.refresh(db_usage)
        return db_usage

    def get_user_type(self, busi_user_id: str) -> str:
        """Determine if user is reseller or business."""
        # Check if it's a reseller
        reseller = self.db.query(Reseller).filter(Reseller.reseller_id == busi_user_id).first()
        if reseller:
            return reseller.role  # 'reseller'
        
        # Check if it's a business user
        business = self.db.query(BusiUser).filter(BusiUser.busi_user_id == busi_user_id).first()
        if business:
            return business.role  # 'business_owner' or similar
            
        return "unknown"

    def get_usage_log(self, usage_id: str) -> Optional[MessageUsageCreditLog]:
        """Get a specific usage log by ID."""
        return self.db.query(MessageUsageCreditLog).filter(
            MessageUsageCreditLog.usage_id == usage_id
        ).first()

    def get_user_usage_logs(
        self,
        busi_user_id: str,
        skip: int = 0,
        limit: int = 100,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[MessageUsageCreditLog]:
        """Get usage logs for a specific user with optional date filtering."""
        query = self.db.query(MessageUsageCreditLog).filter(
            MessageUsageCreditLog.busi_user_id == busi_user_id
        )
        
        if start_date:
            query = query.filter(MessageUsageCreditLog.timestamp >= start_date)
        
        if end_date:
            query = query.filter(MessageUsageCreditLog.timestamp <= end_date)
        
        logs = query.order_by(desc(MessageUsageCreditLog.timestamp)).offset(skip).limit(limit).all()
        
        # Safety: Ensure balance_after is never negative in the response
        for log in logs:
            if log.balance_after < 0:
                log.balance_after = 0
                
        return logs

    def update_usage_log(
        self,
        usage_id: str,
        usage_data: MessageUsageCreditLogUpdate
    ) -> Optional[MessageUsageCreditLog]:
        """Update a usage log entry."""
        db_usage = self.get_usage_log(usage_id)
        
        if not db_usage:
            return None
        
        update_data = usage_data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(db_usage, field, value)
        
        self.db.commit()
        self.db.refresh(db_usage)
        return db_usage

    def delete_usage_log(self, usage_id: str) -> bool:
        """Delete a usage log entry."""
        db_usage = self.get_usage_log(usage_id)
        
        if not db_usage:
            return False
        
        self.db.delete(db_usage)
        self.db.commit()
        return True

    def get_user_current_balance(self, busi_user_id: str) -> float:
        """Get current balance for a user based on their latest usage log."""
        latest_log = self.db.query(MessageUsageCreditLog).filter(
            MessageUsageCreditLog.busi_user_id == busi_user_id
        ).order_by(desc(MessageUsageCreditLog.timestamp)).first()
        
        if latest_log:
            return float(latest_log.balance_after)
        
        return 0.0

    def get_credit_summary(self, busi_user_id: str) -> dict:
        """Get credit summary including total usage, total added, and latest transaction."""
        # Total usage (deductions - positive values)
        total_usage = self.db.query(func.sum(MessageUsageCreditLog.credits_deducted))\
            .filter(and_(
                MessageUsageCreditLog.busi_user_id == str(busi_user_id),
                MessageUsageCreditLog.credits_deducted > 0
            ))\
            .scalar() or 0
            
        # Total added (credits added - negative usage values)
        total_added_raw = self.db.query(func.sum(MessageUsageCreditLog.credits_deducted))\
            .filter(and_(
                MessageUsageCreditLog.busi_user_id == str(busi_user_id),
                MessageUsageCreditLog.credits_deducted < 0
            ))\
            .scalar() or 0
        total_added = abs(total_added_raw)
            
        # Latest deduction (actual usage)
        latest_deduction_log = self.db.query(MessageUsageCreditLog)\
            .filter(and_(
                MessageUsageCreditLog.busi_user_id == str(busi_user_id),
                MessageUsageCreditLog.credits_deducted > 0
            ))\
            .order_by(desc(MessageUsageCreditLog.timestamp))\
            .first()
            
        # Latest transaction (any addition or deduction)
        latest_any_log = self.db.query(MessageUsageCreditLog)\
            .filter(MessageUsageCreditLog.busi_user_id == str(busi_user_id))\
            .order_by(desc(MessageUsageCreditLog.timestamp))\
            .first()
            
        return {
            "total_usage": total_usage,
            "total_added": total_added,
            "latest_deduction": {
                "credits": latest_deduction_log.credits_deducted if latest_deduction_log else 0,
                "timestamp": latest_deduction_log.timestamp if latest_deduction_log else None
            },
            "latest_transaction": {
                "credits": latest_any_log.credits_deducted if latest_any_log else 0,
                "timestamp": latest_any_log.timestamp if latest_any_log else None,
                "message_id": latest_any_log.message_id if latest_any_log else None
            }
        }
    def get_deduction_rate(self, busi_user_id: str) -> float:
        """
        🔥 Determines current deduction rate dynamically.
        Prioritizes user.consumption_rate, then plan.deduction_value.
        """
        try:
            lookup_id = str(busi_user_id)
            user = self.db.query(BusiUser).filter(BusiUser.busi_user_id == lookup_id).first()
            
            if not user:
                # Check if it's a Reseller (Standard Reseller logic)
                from models.reseller import Reseller
                reseller = self.db.query(Reseller).filter(Reseller.reseller_id == lookup_id).first()
                if reseller:
                    return 0.25 # Resellers get wholesale rate
                return 1.0
                
            # 1. HIGHEST PRIORITY: Fetch plan directly if assigned
            if user.plan_id:
                plan = self.db.query(Plan).filter(Plan.plan_id == user.plan_id).first()
                if plan:
                    rate = float(plan.deduction_value) if plan.deduction_value is not None else 1.0
                    # Sync to user cache if missing
                    if not user.consumption_rate or user.consumption_rate != rate:
                        user.consumption_rate = rate
                        self.db.add(user)
                    return rate

            # 2. Use cached consumption_rate if it exists
            if hasattr(user, 'consumption_rate') and user.consumption_rate and user.consumption_rate > 0:
                return float(user.consumption_rate)
            
            # 3. FINAL FALLBACK: Default to standard demo rate
            return 1.0
        except Exception:
            return 1.0

    def deduct_credits(self, busi_user_id: str, message_id: str, amount: Optional[float] = None, timestamp: Optional[datetime] = None, source: str = "single") -> bool:
        """
        🔥 ATOMIC CREDIT DEDUCTION
        Deducts credits from user/reseller wallet and logs the usage.
        If amount is None, it dynamically determines the rate from the user's plan.
        source: "single", "bulk", or "trigger" to track message type
        Returns True if successful, raises exception for insufficient balance.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            lookup_id = str(busi_user_id)
            
            # 1. Fetch user (Try BusiUser first, then Reseller)
            user = self.db.query(BusiUser).filter(BusiUser.busi_user_id == lookup_id).first()
            user_type = "business"
            
            if not user:
                user = self.db.query(Reseller).filter(Reseller.reseller_id == lookup_id).first()
                user_type = "reseller"
                
            if not user:
                logger.error(f"❌ CREDIT ERROR: User {lookup_id} not found.")
                return False

            # 2. Determine Amount if not provided
            if amount is None:
                amount = self.get_deduction_rate(lookup_id)
            
            logger.info(f"💰 DEDUCTION CALCULATION: user={lookup_id}, calculated_amount={amount}, source={source}")

            # 3. Check balance & Update
            if user_type == "business":
                available = float(user.credits_remaining or 0.0)
                if available < amount:
                    raise Exception(f"Insufficient credits. Required: {amount}, Available: {available}.")
                
                user.credits_remaining -= amount
                user.credits_used = float(user.credits_used or 0.0) + amount
                
                new_balance = user.credits_remaining
            else:
                available = float(user.available_credits or 0.0)
                if available < amount:
                    raise Exception(f"Insufficient credits. Required: {amount}, Available: {available}.")
                
                user.available_credits -= amount
                # 🔥 FIX: Reseller uses 'used_credits', NOT 'credits_used'
                user.used_credits = float(user.used_credits or 0.0) + amount
                new_balance = user.available_credits

            # 🔥 NEW: Create Audit Log Entry (Authoritative Source for Dashboard)
            usage_log = MessageUsageCreditLog(
                usage_id=str(uuid.uuid4()), # Ensure string for String(36) column
                busi_user_id=lookup_id,
                message_id=str(message_id),
                credits_deducted=amount,
                balance_after=new_balance,
                source=source,
                timestamp=timestamp or datetime.now(timezone.utc)
            )
            self.db.add(usage_log)

            # Atomic commit for both user update and log creation
            self.db.commit()
            logger.info(f"✅ [CREDIT_DEDUCTION] user={lookup_id}, amount={amount}, balance={new_balance}, log={usage_log.usage_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ [CREDIT_DEDUCTION_ERROR] user={busi_user_id}: {str(e)}")
            raise e
