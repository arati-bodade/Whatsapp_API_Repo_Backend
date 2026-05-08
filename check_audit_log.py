"""
Quick script to check audit logs for specific users.
"""

import sys
import os

# Add the parent directory to the path to import from the backend
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db.session import SessionLocal
from models.audit_log import AuditLog

def check_audit_logs():
    """Check audit logs for specific users."""
    db = SessionLocal()
    
    try:
        # Check all audit logs
        print("=== All Audit Logs ===")
        logs = db.query(AuditLog).all()
        
        print(f"Total logs: {len(logs)}")
        
        for log in logs:
            print(f"\nLog ID: {log.id}")
            print(f"  Affected User ID: {log.affected_user_id}")
            print(f"  Affected User Name: {log.affected_user_name}")
            print(f"  Affected User Email: {log.affected_user_email}")
            print(f"  Action Type: {log.action_type}")
            print(f"  Module: {log.module}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_audit_logs()
