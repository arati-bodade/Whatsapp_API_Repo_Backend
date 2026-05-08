from fastapi import Request
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional, List
from models.busi_user import BusiUser
from models.reseller import Reseller
from models.message import Message
from schemas.busi_user import BusiUserCreateSchema, BusiUserUpdateSchema
from schemas.audit_log import AuditLogCreate
from services.audit_log_service import AuditLogService
from core.security import get_password_hash, verify_password
from services.email_validator import is_email_taken, normalize_email
import uuid


class BusiUserService:
    def __init__(self, db: Session):
        self.db = db

    def create_busi_user(self, busi_user_data: BusiUserCreateSchema, created_by: Optional[str] = None, request: Request = None) -> BusiUser:
        parent_reseller = None
        # Logic for parent lookup based on parent_role
        if busi_user_data.parent_role == "reseller":
            if not busi_user_data.parent_reseller_id:
                 raise ValueError("Parent reseller ID is required for reseller-managed users")
            parent_reseller = self.db.query(Reseller).filter(Reseller.reseller_id == busi_user_data.parent_reseller_id).first()
            if not parent_reseller:
                raise ValueError("Parent reseller not found")
            if parent_reseller.role != "reseller":
                raise ValueError("Parent must be a reseller")
        elif busi_user_data.parent_role == "admin":
             # Direct user, no reseller needed. Admin is the parent.
             pass
        else:
             raise ValueError(f"Invalid parent role: {busi_user_data.parent_role}")

        # Normalize email before validation
        normalized_email = normalize_email(busi_user_data.profile.email)
        busi_user_data.profile.email = normalized_email

        # 1. Global Email check
        if is_email_taken(self.db, normalized_email, request=request):
            raise ValueError("EMAIL_ALREADY_EXISTS")

        # 2. Local check for username/phone
        existing_business = self.db.query(BusiUser).filter(
            or_(
                BusiUser.username == busi_user_data.profile.username,
                BusiUser.phone == busi_user_data.profile.phone
            )
        ).first()
        
        if existing_business:
            raise ValueError("BusiUser with this username or phone already exists")
        
        # Check if GSTIN already exists (if provided)
        if busi_user_data.business.gstin:
            existing_gstin = self.db.query(BusiUser).filter(BusiUser.gstin == busi_user_data.business.gstin).first()
            if existing_gstin:
                raise ValueError("BusiUser with this GSTIN already exists")

        # Create new business
        db_business = BusiUser(
            busi_user_id=str(uuid.uuid4()),
            role=busi_user_data.role,
            status=busi_user_data.status,
            parent_reseller_id=busi_user_data.parent_reseller_id,
            parent_role=busi_user_data.parent_role, # NEW: Track if parent is reseller or admin
            name=busi_user_data.profile.name,
            username=busi_user_data.profile.username,
            email=busi_user_data.profile.email,
            phone=busi_user_data.profile.phone,
            password_hash=get_password_hash(busi_user_data.profile.password),
            business_name=busi_user_data.business.business_name,
            business_description=busi_user_data.business.business_description,
            erp_system=busi_user_data.business.erp_system,
            gstin=busi_user_data.business.gstin,
            full_address=busi_user_data.address.full_address if busi_user_data.address else None,
            pincode=busi_user_data.address.pincode if busi_user_data.address else None,
            country=busi_user_data.address.country if busi_user_data.address else None,
            credits_allocated=(busi_user_data.wallet.credits_allocated if busi_user_data.wallet else 0) or 0,
            credits_used=(busi_user_data.wallet.credits_used if busi_user_data.wallet else 0) or 0,
            credits_remaining=(busi_user_data.wallet.credits_remaining if busi_user_data.wallet else 0) or 0,
            whatsapp_mode=busi_user_data.whatsapp_mode,
            created_by=created_by,
        )

        self.db.add(db_business)
        self.db.commit()
        self.db.refresh(db_business)
        
        # Log to AuditLog
        audit_service = AuditLogService(self.db)
        audit_log = AuditLogCreate(
            reseller_id=db_business.parent_reseller_id if db_business.parent_role == "reseller" else None,
            performed_by_id=db_business.parent_reseller_id or db_business.busi_user_id,
            performed_by_name=parent_reseller.name if parent_reseller else "System/Admin",
            performed_by_role=db_business.parent_role,
            affected_user_id=db_business.busi_user_id,
            affected_user_name=db_business.business_name or db_business.name,
            affected_user_email=db_business.email,
            action_type="CREATE USER",
            module="Users",
            description=f"Created {db_business.parent_role}-direct business user {db_business.business_name}",
            changes_made=[f"initial_role: {db_business.role}", f"initial_credits: {db_business.credits_allocated}"]
        )
        audit_service.create_log(audit_log)
        
        return db_business

    def get_business_by_id(self, business_id: str) -> Optional[BusiUser]:
        return self.db.query(BusiUser).filter(BusiUser.busi_user_id == str(business_id)).first()

    def get_business_by_email(self, email: str) -> Optional[BusiUser]:
        return self.db.query(BusiUser).filter(BusiUser.email == email).first()

    def get_business_by_username(self, username: str) -> Optional[BusiUser]:
        return self.db.query(BusiUser).filter(BusiUser.username == username).first()

    def get_businesses_by_reseller(self, reseller_id: str, skip: int = 0, limit: int = 100) -> List[BusiUser]:
        return self.db.query(BusiUser).filter(
            BusiUser.parent_reseller_id == str(reseller_id)
        ).offset(skip).limit(limit).all()

    def get_all_businesses(self, skip: int = 0, limit: int = 100) -> List[BusiUser]:
        return self.db.query(BusiUser).offset(skip).limit(limit).all()

    def update_busi_user(self, busi_user_id: str, busi_user_data: BusiUserUpdateSchema, reseller_id: Optional[str] = None) -> Optional[BusiUser]:
        db_business = self.get_business_by_id(busi_user_id)
        if not db_business:
            return None

        if reseller_id and db_business.parent_reseller_id != reseller_id:
            raise ValueError("Unauthorized: User does not belong to this reseller")

        # Update basic fields
        if busi_user_data.role is not None:
            db_business.role = busi_user_data.role
        if busi_user_data.status is not None:
            db_business.status = busi_user_data.status
        if busi_user_data.whatsapp_mode is not None:
            db_business.whatsapp_mode = busi_user_data.whatsapp_mode

        # Update profile fields
        if busi_user_data.profile:
            if busi_user_data.profile.name:
                db_business.name = busi_user_data.profile.name
            if busi_user_data.profile.username:
                # Check if username is already taken by another business
                existing_business = self.db.query(BusiUser).filter(
                    BusiUser.username == busi_user_data.profile.username,
                    BusiUser.busi_user_id != busi_user_id
                ).first()
                if existing_business:
                    raise ValueError("Username already taken")
                db_business.username = busi_user_data.profile.username
            if busi_user_data.profile.email:
                # Check if email is already taken by another business
                existing_business = self.db.query(BusiUser).filter(
                    BusiUser.email == busi_user_data.profile.email,
                    BusiUser.busi_user_id != busi_user_id
                ).first()
                if existing_business:
                    raise ValueError("Email already taken")
                db_business.email = busi_user_data.profile.email
            if busi_user_data.profile.phone:
                # Check if phone is already taken by another business
                existing_business = self.db.query(BusiUser).filter(
                    BusiUser.phone == busi_user_data.profile.phone,
                    BusiUser.busi_user_id != busi_user_id
                ).first()
                if existing_business:
                    raise ValueError("Phone number already taken")
                db_business.phone = busi_user_data.profile.phone
            if busi_user_data.profile.password:
                db_business.password_hash = get_password_hash(busi_user_data.profile.password)

        # Update business fields
        if busi_user_data.business:
            if busi_user_data.business.business_name is not None:
                db_business.business_name = busi_user_data.business.business_name
            if busi_user_data.business.organization_type is not None:
                db_business.organization_type = busi_user_data.business.organization_type
            if busi_user_data.business.business_description is not None:
                db_business.business_description = busi_user_data.business.business_description
            if busi_user_data.business.erp_system is not None:
                db_business.erp_system = busi_user_data.business.erp_system
            if busi_user_data.business.gstin is not None:
                db_business.gstin = busi_user_data.business.gstin
            if busi_user_data.business.bank_name is not None:
                db_business.bank_name = busi_user_data.business.bank_name

        # Update address fields
        if busi_user_data.address:
            if busi_user_data.address.full_address is not None:
                db_business.full_address = busi_user_data.address.full_address
            if busi_user_data.address.pincode is not None:
                db_business.pincode = busi_user_data.address.pincode
            if busi_user_data.address.country is not None:
                db_business.country = busi_user_data.address.country

        # Update wallet fields
        if busi_user_data.wallet:
            if busi_user_data.wallet.credits_allocated is not None:
                db_business.credits_allocated = busi_user_data.wallet.credits_allocated
            if busi_user_data.wallet.credits_used is not None:
                db_business.credits_used = busi_user_data.wallet.credits_used
            if busi_user_data.wallet.credits_remaining is not None:
                db_business.credits_remaining = busi_user_data.wallet.credits_remaining

        # Track changes for audit log
        changes_made = []
        if busi_user_data.status is not None and busi_user_data.status != db_business.status:
            changes_made.append(f"status: {db_business.status} → {busi_user_data.status}")
        if busi_user_data.role is not None and busi_user_data.role != db_business.role:
            changes_made.append(f"role: {db_business.role} → {busi_user_data.role}")
        if busi_user_data.wallet and busi_user_data.wallet.credits_allocated is not None:
            changes_made.append(f"credits_allocated: {busi_user_data.wallet.credits_allocated}")

        self.db.commit()
        
        # Create audit log if there were changes
        if changes_made:
            audit_service = AuditLogService(self.db)
            audit_log = AuditLogCreate(
                reseller_id=reseller_id or db_business.parent_reseller_id,
                performed_by_id=reseller_id or db_business.parent_reseller_id,
                performed_by_name="System",  # This would be the actual user performing the action
                performed_by_role="admin",  # This would be the actual role
                affected_user_id=db_business.busi_user_id,
                affected_user_name=db_business.business_name or db_business.name,
                affected_user_email=db_business.email,
                action_type="UPDATE USER" if not changes_made or "credits" not in str(changes_made) else "UPDATE USER PLAN",
                module="Users",
                description=f"Updated user {db_business.business_name or db_business.name}",
                changes_made=changes_made
            )
            audit_service.create_log(audit_log)
        
        self.db.refresh(db_business)
        return db_business

    def delete_busi_user(self, busi_user_id: str, reseller_id: Optional[str] = None) -> bool:
        db_business = self.get_business_by_id(busi_user_id)
        if not db_business:
            return False

        if reseller_id and db_business.parent_reseller_id != reseller_id:
            raise ValueError("Unauthorized: User does not belong to this reseller")

        # Log to AuditLog before deletion
        audit_service = AuditLogService(self.db)
        audit_log = AuditLogCreate(
            reseller_id=db_business.parent_reseller_id,
            performed_by_id=reseller_id or db_business.parent_reseller_id,
            performed_by_name="Reseller", # Placeholder
            performed_by_role="reseller",
            affected_user_id=db_business.busi_user_id,
            affected_user_name=db_business.business_name or db_business.name,
            affected_user_email=db_business.email,
            action_type="DELETE USER",
            module="Users",
            description=f"Deleted business user {db_business.business_name}",
            changes_made=["User record removed"]
        )
        audit_service.create_log(audit_log)

        self.db.delete(db_business)
        self.db.commit()
        return True

    def authenticate_business(self, email: str, password: str) -> Optional[BusiUser]:
        email = email.lower().strip()
        business = self.get_business_by_email(email)
        if not business:
            return None
        
        # 1. Try standard Bcrypt verification
        if verify_password(password, business.password_hash):
            return business
        
        # 2. Check for legacy PLAIN TEXT password
        if business.password_hash == password.strip():
            logger.warning(f"Found plain text password for user {email}. Migrating...")
            # Migrate to Bcrypt
            business.password_hash = get_password_hash(password.strip())
            try:
                self.db.commit()
                self.db.refresh(business)
                logger.info(f"Password migrated successfully for {email}")
            except Exception as e:
                logger.error(f"Failed to migrate password for {email}: {e}")
            return business

        return None

    def authenticate_busi_user(self, email: str, password: str) -> Optional[BusiUser]:
        """Alias for authenticate_business to maintain API consistency."""
        return self.authenticate_business(email, password)

    def get_all_busi_useres(self, skip: int = 0, limit: int = 100) -> List[BusiUser]:
        """Get all business users with pagination."""
        return self.db.query(BusiUser).offset(skip).limit(limit).all()

    def get_busi_useres_by_reseller(self, reseller_id: str, skip: int = 0, limit: int = 100) -> List[BusiUser]:
        """Get all business users under a specific reseller with pagination."""
        return (
            self.db.query(BusiUser)
            .filter(BusiUser.parent_reseller_id == str(reseller_id))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_all_busi_useres(self, skip: int = 0, limit: int = 100) -> List[BusiUser]:
        """Get all business users with pagination."""
        return self.db.query(BusiUser).offset(skip).limit(limit).all()

    def get_busi_user_by_id(self, busi_user_id: str) -> Optional[BusiUser]:
        """Get a specific business user by ID."""
        return self.db.query(BusiUser).filter(BusiUser.busi_user_id == str(busi_user_id)).first()

    def get_reseller_analytics(self, reseller_id: str) -> dict:
        """Get analytics for a reseller's business users."""
        from models.device import Device, SessionStatus
        from datetime import datetime, timezone

        # 1. Basic counts
        total_users = self.db.query(BusiUser).filter(BusiUser.parent_reseller_id == str(reseller_id)).count()
        active_users = self.db.query(BusiUser).filter(
            BusiUser.parent_reseller_id == str(reseller_id),
            BusiUser.status == "active"
        ).count()
        
        # 2. Connectivity stats (JOIN BusiUser with Device)
        # A user is "connected" if they have at least one device in 'connected' status
        connected_users_count = self.db.query(BusiUser.busi_user_id).join(
            Device, BusiUser.busi_user_id == Device.busi_user_id
        ).filter(
            BusiUser.parent_reseller_id == str(reseller_id),
            Device.session_status == SessionStatus.connected,
            Device.is_active == True
        ).distinct().count()

        # Users who are not connected
        disconnected_users_count = total_users - connected_users_count

        # 3. Plan stats
        # Users whose plan has expired
        now = datetime.now(timezone.utc)
        plan_expired_users_count = self.db.query(BusiUser).filter(
            BusiUser.parent_reseller_id == str(reseller_id),
            BusiUser.plan_expiry < now
        ).count()

        # 4. Message usage
        # Fetch user IDs as strings
        user_ids_query = self.db.query(BusiUser.busi_user_id).filter(BusiUser.parent_reseller_id == str(reseller_id))
        user_ids = [str(uid[0]) for uid in user_ids_query.all()]
        
        messages_sent = 0
        if user_ids:
            # Replaced Message with MessageUsageCreditLog if it's more accurate for billing
            from models.message import Message # Re-import inside just in case
            messages_sent = self.db.query(Message).filter(Message.busi_user_id.in_(user_ids)).count()

        return {
            "total_users": total_users,
            "active_users": active_users,
            "connected_users": connected_users_count,
            "disconnected_users": disconnected_users_count,
            "plan_expired_users": plan_expired_users_count,
            "messages_sent": messages_sent
        }
