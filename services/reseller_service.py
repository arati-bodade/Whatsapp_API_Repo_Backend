from fastapi import Request
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional, List
from models.reseller import Reseller
from schemas.reseller import ResellerCreateSchema, ResellerUpdateSchema
from core.security import get_password_hash, verify_password
from services.audit_log_service import AuditLogService
from schemas.audit_log import AuditLogCreate
from services.email_validator import is_email_taken, normalize_email
import uuid


class ResellerService:
    def __init__(self, db: Session):
        self.db = db

    def create_reseller(self, reseller_data: ResellerCreateSchema, created_by: Optional[str] = None, request: Request = None) -> Reseller:
        """Create a new reseller."""
        # Normalize email before validation
        normalized_email = normalize_email(reseller_data.profile.email)
        reseller_data.profile.email = normalized_email

        # 1. Global Email check
        if is_email_taken(self.db, normalized_email, request=request):
            raise ValueError("EMAIL_ALREADY_EXISTS")

        # 2. Local check for username/phone
        existing_reseller = self.db.query(Reseller).filter(
            or_(
                Reseller.username == reseller_data.profile.username,
                Reseller.phone == reseller_data.profile.phone
            )
        ).first()
        
        if existing_reseller:
            raise ValueError("Reseller with this username or phone already exists")
        
        # Check if GSTIN already exists (if provided)
        if reseller_data.business and reseller_data.business.gstin:
            existing_gstin = self.db.query(Reseller).filter(Reseller.gstin == reseller_data.business.gstin).first()
            if existing_gstin:
                raise ValueError("Reseller with this GSTIN already exists")

        # Create new reseller
        db_reseller = Reseller(
            reseller_id=str(uuid.uuid4()),
            role=reseller_data.role,
            status=reseller_data.status,
            name=reseller_data.profile.name,
            username=reseller_data.profile.username,
            email=reseller_data.profile.email,
            phone=reseller_data.profile.phone,
            password_hash=get_password_hash(reseller_data.profile.password),
            business_name=reseller_data.business.business_name if reseller_data.business else None,
            organization_type=reseller_data.business.organization_type if reseller_data.business else None,
            business_description=reseller_data.business.business_description if reseller_data.business else None,
            erp_system=reseller_data.business.erp_system if reseller_data.business else None,
            gstin=reseller_data.business.gstin if reseller_data.business else None,
            full_address=reseller_data.address.full_address if reseller_data.address else None,
            pincode=reseller_data.address.pincode if reseller_data.address else None,
            country=reseller_data.address.country if reseller_data.address else None,
            bank_name=reseller_data.bank.bank_name if reseller_data.bank else None,
            total_credits=reseller_data.wallet.total_credits if reseller_data.wallet else 0,
            available_credits=reseller_data.wallet.available_credits if reseller_data.wallet else 0,
            used_credits=reseller_data.wallet.used_credits if reseller_data.wallet else 0,
            created_by=created_by,
        )

        self.db.add(db_reseller)
        self.db.commit()
        self.db.refresh(db_reseller)
        
        # Log to AuditLog
        audit_service = AuditLogService(self.db)
        audit_log = AuditLogCreate(
            reseller_id=db_reseller.reseller_id,
            performed_by_id=db_reseller.reseller_id, # Self-registered or Admin-created
            performed_by_name=db_reseller.name or "Reseller",
            performed_by_role="reseller",
            affected_user_id=db_reseller.reseller_id,
            affected_user_name=db_reseller.name or "Reseller",
            affected_user_email=db_reseller.email,
            action_type="REGISTER",
            module="Reseller",
            description=f"Reseller {db_reseller.name} registered",
            changes_made=["Reseller created"]
        )
        audit_service.create_log(audit_log)
        
        return db_reseller

    def get_reseller_by_id(self, reseller_id: str) -> Optional[Reseller]:
        return self.db.query(Reseller).filter(Reseller.reseller_id == str(reseller_id)).first()

    def get_reseller_by_email(self, email: str) -> Optional[Reseller]:
        return self.db.query(Reseller).filter(Reseller.email == email).first()

    def get_reseller_by_username(self, username: str) -> Optional[Reseller]:
        return self.db.query(Reseller).filter(Reseller.username == username).first()

    def get_resellers(self, skip: int = 0, limit: int = 100) -> List[Reseller]:
        return self.db.query(Reseller).offset(skip).limit(limit).all()

    def update_reseller(self, reseller_id: str, reseller_data: ResellerUpdateSchema) -> Optional[Reseller]:
        db_reseller = self.get_reseller_by_id(reseller_id)
        if not db_reseller:
            return None

        updates_made = []

        # Update basic fields
        if reseller_data.role is not None:
            if db_reseller.role != reseller_data.role:
                updates_made.append(f"role: {db_reseller.role} → {reseller_data.role}")
            db_reseller.role = reseller_data.role
        if reseller_data.status is not None:
            if db_reseller.status != reseller_data.status:
                updates_made.append(f"status: {db_reseller.status} → {reseller_data.status}")
            db_reseller.status = reseller_data.status

        # Update profile fields
        if reseller_data.profile:
            if reseller_data.profile.name:
                db_reseller.name = reseller_data.profile.name
            if reseller_data.profile.username:
                # Check if username is already taken by another reseller
                existing_reseller = self.db.query(Reseller).filter(
                    Reseller.username == reseller_data.profile.username,
                    Reseller.reseller_id != str(reseller_id)
                ).first()
                if existing_reseller:
                    raise ValueError("Username already taken")
                db_reseller.username = reseller_data.profile.username
            if reseller_data.profile.email:
                # Check if email is already taken by another reseller
                existing_reseller = self.db.query(Reseller).filter(
                    Reseller.email == reseller_data.profile.email,
                    Reseller.reseller_id != str(reseller_id)
                ).first()
                if existing_reseller:
                    raise ValueError("Email already taken")
                db_reseller.email = reseller_data.profile.email
            if reseller_data.profile.phone:
                # Check if phone is already taken by another reseller
                existing_reseller = self.db.query(Reseller).filter(
                    Reseller.phone == reseller_data.profile.phone,
                    Reseller.reseller_id != str(reseller_id)
                ).first()
                if existing_reseller:
                    raise ValueError("Phone number already taken")
                db_reseller.phone = reseller_data.profile.phone
            if reseller_data.profile.password:
                db_reseller.password_hash = get_password_hash(reseller_data.profile.password)

        # Update business fields
        if reseller_data.business:
            if reseller_data.business.business_name is not None:
                db_reseller.business_name = reseller_data.business.business_name
            if reseller_data.business.organization_type is not None:
                db_reseller.organization_type = reseller_data.business.organization_type
            if reseller_data.business.business_description is not None:
                db_reseller.business_description = reseller_data.business.business_description
            if reseller_data.business.erp_system is not None:
                db_reseller.erp_system = reseller_data.business.erp_system
            if reseller_data.business.gstin is not None:
                db_reseller.gstin = reseller_data.business.gstin

        # Update address fields
        if reseller_data.address:
            if reseller_data.address.full_address is not None:
                db_reseller.full_address = reseller_data.address.full_address
            if reseller_data.address.pincode is not None:
                db_reseller.pincode = reseller_data.address.pincode
            if reseller_data.address.country is not None:
                db_reseller.country = reseller_data.address.country

        # Update bank fields
        if reseller_data.bank:
            if reseller_data.bank.bank_name is not None:
                db_reseller.bank_name = reseller_data.bank.bank_name

        # Update wallet fields
        # Update wallet fields with validation
        if reseller_data.wallet:
            total = db_reseller.total_credits
            available = db_reseller.available_credits
            used = db_reseller.used_credits

            if reseller_data.wallet.total_credits is not None:
                total = reseller_data.wallet.total_credits
            if reseller_data.wallet.available_credits is not None:
                available = reseller_data.wallet.available_credits
            if reseller_data.wallet.used_credits is not None:
                used = reseller_data.wallet.used_credits
            
            # Validation: internal consistency
            # We assume total = available + used usually, but sometimes total credits can be increased without immediately assigning them.
            # Stricter check: available + used <= total ? Or simply non-negative?
            # Model fields have constraints in schema, but good to check logic here.
            
            if total < 0 or available < 0 or used < 0:
                 raise ValueError("Credit values cannot be negative")

            # Simple consistency check: if we are updating strict accounting
            # For now, we trust the input but ensure they are not negative. 
            # Ideally, specific methods like 'add_credits' should be used instead of direct update.
            
            db_reseller.total_credits = total
            db_reseller.available_credits = available
            db_reseller.used_credits = used

        self.db.commit()
            
        # Log to AuditLog if changes were made
        if updates_made:
            audit_service = AuditLogService(self.db)
            audit_log = AuditLogCreate(
                reseller_id=db_reseller.reseller_id,
                performed_by_id=db_reseller.reseller_id, # This should ideally be the user who performed the update
                performed_by_name=db_reseller.name or "Reseller",
                performed_by_role="reseller",
                affected_user_id=db_reseller.reseller_id,
                affected_user_name=db_reseller.name or "Reseller",
                affected_user_email=db_reseller.email,
                action_type="UPDATE PROFILE",
                module="Reseller",
                description="Profile details updated",
                changes_made=updates_made
            )
            audit_service.create_log(audit_log)

        self.db.refresh(db_reseller)
        return db_reseller

    def delete_reseller(self, reseller_id: str) -> bool:
        """Delete a reseller by ID."""
        db_reseller = self.get_reseller_by_id(reseller_id)
        if not db_reseller:
            return False

        # Log to AuditLog before deletion
        audit_service = AuditLogService(self.db)
        audit_log = AuditLogCreate(
            reseller_id=db_reseller.reseller_id,
            performed_by_id=db_reseller.reseller_id, # Should ideally be the admin who deleted
            performed_by_name="Admin", # Placeholder, actual admin name should be passed
            performed_by_role="admin",
            affected_user_id=db_reseller.reseller_id,
            affected_user_name=db_reseller.name or "Reseller",
            affected_user_email=db_reseller.email,
            action_type="DELETE ACCOUNT",
            module="Reseller",
            description=f"Reseller {db_reseller.name} deleted",
            changes_made=["Reseller record removed"]
        )
        audit_service.create_log(audit_log)

        self.db.delete(db_reseller)
        self.db.commit()
        return True

    def authenticate_reseller(self, email: str, password: str) -> Optional[Reseller]:
        reseller = self.get_reseller_by_email(email)
        if not reseller:
            return None
        if not verify_password(password, reseller.password_hash):
            return None
        return reseller
