import sys
import os
import uuid
from sqlalchemy.orm import Session

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

from db.session import SessionLocal
from models.busi_user import BusiUser
from models.google_sheet import GoogleSheet
from models.campaign import Campaign
from models.audit_log import AuditLog

def delete_specific_user(email):
    db = SessionLocal()
    try:
        user = db.query(BusiUser).filter(BusiUser.email == email).first()
        if not user:
            print(f"❌ User with email {email} not found.")
            return

        user_id = user.busi_user_id
        print(f"🔍 Found user: {user.name} ({user_id})")

        # Ensure Audit Logs don't block deletion
        print("🧹 Cleaning up Audit Logs...")
        db.query(AuditLog).filter(AuditLog.affected_user_id == user_id).update({"affected_user_id": None})
        db.query(AuditLog).filter(AuditLog.reseller_id == user_id).update({"reseller_id": None})
        
        # Delete the user (rely on SQLAlchemy cascades for the rest)
        print(f"🗑️ Deleting user {user.name}...")
        db.delete(user)
        db.commit()
        print(f"✅ User {email} deleted successfully!")

    except Exception as e:
        db.rollback()
        print(f"❌ Failed to delete user: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    delete_specific_user("tushar.nimbolkar@gmail.com")
