import re
from fastapi import Request
from sqlalchemy.orm import Session
from sqlalchemy import or_
from models.busi_user import BusiUser
from models.reseller import Reseller
from models.admin import MasterAdmin
from services.audit_log_service import AuditLogService
from schemas.audit_log import AuditLogCreate

def normalize_email(email: str) -> str:
    """
    Centralized email normalization:
    - trimes spaces
    - removes accidental double spaces
    - converts to lowercase
    - validates format securely
    """
    if not email:
        raise ValueError("Please enter a valid email address.")
        
    # Trim spaces and replace multiple internal spaces with none or single (emails shouldn't have internal spaces)
    email_clean = re.sub(r'\s+', '', email.strip().lower())
    
    # Strict email validation regex
    email_regex = r"^[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$"
    if not re.match(email_regex, email_clean):
        raise ValueError("Please enter a valid email address.")
        
    return email_clean

def is_email_taken(db: Session, email: str, request: Request = None, context: str = "REGISTRATION") -> bool:
    """
    Check if the given email is already registered across any role.
    This ensures uniqueness across MasterAdmin, Reseller, and BusiUser tables.
    Also logs the duplicate attempt if found.
    """
    try:
        email_clean = normalize_email(email)
    except ValueError:
        raise
    
    # Check MasterAdmin
    is_taken = False
    role_found = None
    if db.query(MasterAdmin).filter(MasterAdmin.email.ilike(email_clean)).first():
        is_taken = True
        role_found = "admin"
    elif db.query(Reseller).filter(Reseller.email.ilike(email_clean)).first():
        is_taken = True
        role_found = "reseller"
    elif db.query(BusiUser).filter(BusiUser.email.ilike(email_clean)).first():
        is_taken = True
        role_found = "busi_user"
        
    if is_taken:
        # Audit logging for duplicate attempt
        ip_address = request.client.host if request and request.client else "Unknown IP"
        audit_service = AuditLogService(db)
        audit_log = AuditLogCreate(
            reseller_id=None,
            performed_by_id="SYSTEM",
            performed_by_name="System",
            performed_by_role="system",
            affected_user_id="UNKNOWN",
            affected_user_name="Duplicate Attempt",
            affected_user_email=email_clean,
            action_type="BLOCKED_REGISTRATION",
            module="Security",
            description=f"Blocked duplicate registration attempt for {email_clean} ({context})",
            changes_made=[f"IP: {ip_address}", f"Existing Role: {role_found}"]
        )
        try:
            audit_service.create_log(audit_log)
        except Exception:
            pass # Failsafe
        
        return True
        
    return False
