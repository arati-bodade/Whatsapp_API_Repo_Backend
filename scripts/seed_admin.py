import os
import sys
import uuid
from sqlalchemy.orm import Session

# Add the project root to sys.path to import modules correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.session import SessionLocal
from models.admin import MasterAdmin
from core.security import get_password_hash

def seed_admin():
    db = SessionLocal()
    try:
        # Configuration
        ADMIN_EMAIL = "adminlogin6631@gmail.com"
        ADMIN_PASSWORD = "Admin@6631"
        ADMIN_USERNAME = "System_Admin"
        
        # Check if admin already exists
        existing_admin = db.query(MasterAdmin).filter(
            (MasterAdmin.email == ADMIN_EMAIL) | (MasterAdmin.username == ADMIN_USERNAME)
        ).first()
        
        if existing_admin:
            print(f"ℹ️ Admin with email {ADMIN_EMAIL} or username {ADMIN_USERNAME} already exists.")
            # Update password just in case it was changed
            existing_admin.password_hash = get_password_hash(ADMIN_PASSWORD)
            db.commit()
            print("✅ Admin password updated to match requirements.")
            return

        # Create new admin
        new_admin = MasterAdmin(
            admin_id=uuid.uuid4(),
            username=ADMIN_USERNAME,
            email=ADMIN_EMAIL,
            password_hash=get_password_hash(ADMIN_PASSWORD),
            name="Platform Administrator",
            phone="+91 0000000000",
            business_name="WhatsApp Platform Enterprise",
            bio="System administrator for the WhatsApp Platform. Responsible for global operations and user management.",
            location="Cloud Infrastructure"
        )
        
        db.add(new_admin)
        db.commit()
        db.refresh(new_admin)
        print(f"✅ Successfully seeded default admin: {ADMIN_EMAIL}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding admin: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Seeding administrative data...")
    seed_admin()
