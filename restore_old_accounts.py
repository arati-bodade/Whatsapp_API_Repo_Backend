import sys
import os
import uuid
from datetime import datetime, timezone, timedelta

# Add the current directory to sys.path
sys.path.append(os.getcwd())

from db.session import SessionLocal
from models.admin import MasterAdmin
from models.busi_user import BusiUser
from models.plan import Plan
from core.security import get_password_hash

def restore():
    db = SessionLocal()
    try:
        print("Restoring Old Admin and User...")

        # 1. Remove temporary accounts
        db.query(MasterAdmin).filter(MasterAdmin.email == "admin@example.com").delete()
        db.query(BusiUser).filter(BusiUser.email == "user@example.com").delete()
        db.commit()

        # 2. Get/Create Business Plan
        business_plan = db.query(Plan).filter(Plan.name == "Business Starter").first()
        if not business_plan:
            business_plan = Plan(
                plan_id=uuid.uuid4(),
                name="Business Starter",
                description="Starter plan for small businesses",
                price=499.0,
                credits_offered=5000,
                validity_days=30,
                plan_category="BUSINESS",
                status="active"
            )
            db.add(business_plan)
            db.commit()

        # 3. Restore Old Master Admin
        ADMIN_EMAIL = "adminlogin6631@gmail.com"
        ADMIN_PASSWORD = "Admin@6631"
        ADMIN_USERNAME = "System_Admin"
        
        old_admin = db.query(MasterAdmin).filter(MasterAdmin.email == ADMIN_EMAIL).first()
        if not old_admin:
            old_admin = MasterAdmin(
                admin_id=uuid.uuid4(),
                username=ADMIN_USERNAME,
                email=ADMIN_EMAIL,
                password_hash=get_password_hash(ADMIN_PASSWORD),
                name="Platform Administrator",
                phone="+91 0000000000",
                business_name="WhatsApp Platform Enterprise",
                bio="System administrator resurrected from previous logs.",
                location="Cloud Infrastructure"
            )
            db.add(old_admin)
            print(f"SUCCESS: Restored Admin: {ADMIN_EMAIL}")
        else:
            print(f"INFO: Admin {ADMIN_EMAIL} already exists.")

        # 4. Restore Old Business User
        USER_EMAIL = "lungeom39@gmail.com"
        USER_PASSWORD = "user123" # Fallback password if unknown
        
        old_user = db.query(BusiUser).filter(BusiUser.email == USER_EMAIL).first()
        if not old_user:
            old_user = BusiUser(
                busi_user_id=uuid.uuid4(),
                name="Om Lunge",
                username="om_lunge",
                email=USER_EMAIL,
                phone="9100000000",
                password_hash=get_password_hash(USER_PASSWORD),
                business_name="Lunge Enterprises",
                role="business_owner",
                status="active",
                plan_id=business_plan.plan_id,
                plan_name=business_plan.name,
                credits_allocated=1000,
                credits_remaining=1000,
                plan_expiry=datetime.now(timezone.utc) + timedelta(days=365),
                whatsapp_mode="unofficial"
            )
            db.add(old_user)
            print(f"SUCCESS: Restored User: {USER_EMAIL}")
        else:
            print(f"INFO: User {USER_EMAIL} already exists.")

        db.commit()
        print("\nFINISHED: All accounts restored successfully!")
        print(f"Credentials - Admin: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
        print(f"Credentials - User:  {USER_EMAIL} / {USER_PASSWORD}")

    except Exception as e:
        print(f"ERROR: Restoration failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    restore()
