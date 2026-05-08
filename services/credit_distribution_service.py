from sqlalchemy.orm import Session
from sqlalchemy import desc
from models.credit_distribution import CreditDistribution
from models.reseller import Reseller
from models.busi_user import BusiUser
from schemas.credit_distribution import CreditDistributionCreateSchema
from schemas.audit_log import AuditLogCreate
from services.audit_log_service import AuditLogService
from fastapi import HTTPException, status
from datetime import datetime
import uuid

class CreditDistributionService:
    def __init__(self, db: Session):
        self.db = db

    def distribute_credits(self, data: CreditDistributionCreateSchema, current_reseller_id: str) -> CreditDistribution:
        """
        Distribute credits from a reseller to a business user.
        - Validates reseller has enough credits (available_credits).
        - Validates business user exists and belongs to reseller.
        - Updates balances atomically.
        - Logs the distribution.
        """
        # 1. Fetch Reseller
        reseller = self.db.query(Reseller).filter(Reseller.reseller_id == current_reseller_id).first()
        if not reseller:
            raise HTTPException(status_code=404, detail="Reseller not found")

        # 2. Reseller Validation
        if reseller.available_credits < data.credits_shared:
            raise HTTPException(
                status_code=400, 
                detail=f"Insufficient credits. Available: {reseller.available_credits}, Required: {data.credits_shared}"
            )

        # 3. Fetch Business User
        business_user = self.db.query(BusiUser).filter(BusiUser.busi_user_id == data.to_business_user_id).first()
        if not business_user:
            raise HTTPException(status_code=404, detail="Business User not found")

        # 4. Access Validation
        if business_user.parent_reseller_id != reseller.reseller_id:
            raise HTTPException(status_code=403, detail="You can only distribute credits to your own business users")

        try:
            # 5. Atomic Update (using session transaction context implicitly via flush/commit)
            
            # Deduct from Reseller
            reseller.available_credits -= data.credits_shared
            reseller.used_credits = (reseller.used_credits or 0) + data.credits_shared
            # Note: total_credits remains same, as it represents what the ADMIN gave the reseller. 
            # OR does it represent what the reseller OWNS? 
            # Usually Reseller buys credits (Total increases), then distributes (Available decreases, User's Allocated increases).
            # If reseller.available_credits is what they have left to give, then logic is correct.

            # Add to Business User
            business_user.credits_allocated += data.credits_shared
            business_user.credits_remaining += data.credits_shared
            # credits_used remains same until they send messages.

            # 6. Create Log Entry
            distribution = CreditDistribution(
                distribution_id=f"dist-{uuid.uuid4().hex[:12]}",
                from_reseller_id=reseller.reseller_id,
                to_business_user_id=business_user.busi_user_id,
                credits_shared=data.credits_shared
            )
            self.db.add(distribution)

            # 6a. Create Usage Logs (for transaction history visibility)
            from models.message_usage import MessageUsageCreditLog
            
            # Log for Reseller (deduction)
            reseller_log = MessageUsageCreditLog(
                usage_id=str(uuid.uuid4()),
                busi_user_id=str(reseller.reseller_id),
                message_id=f"DIST-TO-{business_user.business_name or 'USER'}",
                credits_deducted=data.credits_shared, 
                balance_after=reseller.available_credits,
                source="distribution", # 🔥 MARK AS DISTRIBUTION
                timestamp=datetime.now()
            )
            self.db.add(reseller_log)

            # Log for Business User (addition)
            business_log = MessageUsageCreditLog(
                usage_id=str(uuid.uuid4()),
                busi_user_id=str(business_user.busi_user_id),
                message_id=f"DIST-FROM-{reseller.name or 'RESELLER'}",
                credits_deducted=-data.credits_shared, # Negative = Added
                balance_after=business_user.credits_remaining,
                source="distribution", # 🔥 MARK AS DISTRIBUTION
                timestamp=datetime.now()
            )
            self.db.add(business_log)
            
            # 7. Create Audit Log
            audit_service = AuditLogService(self.db)
            audit_log = AuditLogCreate(
                reseller_id=reseller.reseller_id,
                performed_by_id=reseller.reseller_id,
                performed_by_name=reseller.name or "Reseller",
                performed_by_role="reseller",
                affected_user_id=business_user.busi_user_id,
                affected_user_name=business_user.business_name or "Business User",
                affected_user_email=business_user.email,
                action_type="CREDIT ALLOCATION",
                module="Credits",
                description=f"Allocated {data.credits_shared} credits to {business_user.business_name}",
                changes_made=[f"credits_allocated: +{data.credits_shared}", f"available_credits: -{data.credits_shared}"]
            )
            audit_service.create_log(audit_log)
            
            self.db.commit()
            self.db.refresh(distribution)
            
            return distribution

        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Transaction failed: {str(e)}")

    def get_history_by_reseller(self, reseller_id: str, skip: int = 0, limit: int = 100):
        return self.db.query(CreditDistribution)\
            .filter(CreditDistribution.from_reseller_id == reseller_id)\
            .order_by(desc(CreditDistribution.shared_at))\
            .offset(skip)\
            .limit(limit)\
            .all()

    def get_history_by_business(self, business_id: str, skip: int = 0, limit: int = 100):
        return self.db.query(CreditDistribution)\
            .filter(CreditDistribution.to_business_user_id == business_id)\
            .order_by(desc(CreditDistribution.shared_at))\
            .offset(skip)\
            .limit(limit)\
            .all()
