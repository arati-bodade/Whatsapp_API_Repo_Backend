"""
Backfill script to populate missing emails in audit logs.
This script updates audit logs where affected_user_email is NULL or "N/A"
by fetching the email from the corresponding user record.
"""

import sys
import os

# Add the parent directory to the path to import from the backend
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db.session import SessionLocal
from models.audit_log import AuditLog
from models.busi_user import BusiUser
from models.reseller import Reseller

def backfill_audit_emails():
    """Backfill missing emails in audit logs."""
    db = SessionLocal()
    
    try:
        # Find all audit logs where affected_user_email is NULL or "N/A"
        # But only if they have an affected_user_name (to avoid system logs)
        audit_logs = db.query(AuditLog).filter(
            (AuditLog.affected_user_email.is_(None)) | 
            (AuditLog.affected_user_email == "N/A")
        ).filter(
            AuditLog.affected_user_name.isnot(None)
        ).filter(
            AuditLog.affected_user_name != "N/A"
        ).all()
        
        print(f"Found {len(audit_logs)} audit logs with missing emails")
        
        updated_count = 0
        not_found_count = 0
        
        for log in audit_logs:
            # First, try to find by ID if available
            if log.affected_user_id:
                # Try to find the user in BusiUser table
                busi_user = db.query(BusiUser).filter(
                    BusiUser.busi_user_id == str(log.affected_user_id)
                ).first()
                
                if busi_user and busi_user.email:
                    log.affected_user_email = busi_user.email
                    updated_count += 1
                    print(f"Updated log {log.id}: {log.affected_user_name} -> {busi_user.email} (by ID)")
                    continue
                
                # Try to find the user in Reseller table
                reseller = db.query(Reseller).filter(
                    Reseller.reseller_id == str(log.affected_user_id)
                ).first()
                
                if reseller and reseller.email:
                    log.affected_user_email = reseller.email
                    updated_count += 1
                    print(f"Updated log {log.id}: {log.affected_user_name} -> {reseller.email} (by ID)")
                    continue
            
            # If not found by ID, try to find by name
            if log.affected_user_name:
                # Try to find the user in BusiUser table by name or business_name
                busi_user = db.query(BusiUser).filter(
                    (BusiUser.name == log.affected_user_name) |
                    (BusiUser.business_name == log.affected_user_name)
                ).first()
                
                if busi_user and busi_user.email:
                    log.affected_user_email = busi_user.email
                    updated_count += 1
                    print(f"Updated log {log.id}: {log.affected_user_name} -> {busi_user.email} (by name)")
                    continue
                
                # Try to find the user in Reseller table by name
                reseller = db.query(Reseller).filter(
                    Reseller.name == log.affected_user_name
                ).first()
                
                if reseller and reseller.email:
                    log.affected_user_email = reseller.email
                    updated_count += 1
                    print(f"Updated log {log.id}: {log.affected_user_name} -> {reseller.email} (by name)")
                    continue
            
            # User not found in either table
            not_found_count += 1
            print(f"User not found for log {log.id}: {log.affected_user_name} (ID: {log.affected_user_id})")
        
        # Commit the changes
        db.commit()
        
        print(f"\n=== Summary ===")
        print(f"Total logs processed: {len(audit_logs)}")
        print(f"Successfully updated: {updated_count}")
        print(f"User not found: {not_found_count}")
        
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    backfill_audit_emails()
