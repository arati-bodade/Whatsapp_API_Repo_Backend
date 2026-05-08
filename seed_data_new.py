import sys
import os
import uuid
from datetime import datetime, timedelta, timezone

# Add the current directory to sys.path
sys.path.append(os.getcwd())

from db.session import SessionLocal
from models.admin import MasterAdmin
from models.busi_user import BusiUser
from models.reseller import Reseller
from models.plan import Plan
from core.security import get_password_hash

def seed():
    db = SessionLocal()
    try:
        print("Seeding database...")

        # 1. Create Business Plan
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
                status="active",
                created_at=datetime.now(timezone.utc)
            )
            db.add(business_plan)
        
        # 2. Create Admin Plan
        admin_plan = db.query(Plan).filter(Plan.name == "Super Admin Plan").first()
        if not admin_plan:
            admin_plan = Plan(
                plan_id=uuid.uuid4(),
                name="Super Admin Plan",
                description="Unlimited administrative plan",
                price=0,
                credits_offered=999999,
                validity_days=365,
                plan_category="ADMIN",
                status="active"
            )
            db.add(admin_plan)
        
        db.commit()

        # 3. Create Master Admin
        admin = MasterAdmin(
            admin_id=uuid.uuid4(),
            name="Master Admin",
            username="admin",
            email="admin@example.com",
            password_hash=get_password_hash("admin123"),
            created_at=datetime.now(timezone.utc)
        )
        db.add(admin)

        # 4. Create a Business User
        user = BusiUser(
            busi_user_id=uuid.uuid4(),
            name="Test Business",
            username="business",
            email="user@example.com",
            phone="1234567890",
            password_hash=get_password_hash("user123"),
            business_name="Test Enterprise",
            role="business_owner",
            status="active",
            plan_id=business_plan.plan_id,
            plan_name=business_plan.name,
            credits_allocated=5000,
            credits_remaining=5000,
            plan_expiry=datetime.now(timezone.utc) + timedelta(days=30),
            whatsapp_mode="unofficial",
            created_at=datetime.now(timezone.utc)
        )
        db.add(user)

        db.commit()
        print("Database seeded successfully!")
        print(f"Admin: admin@example.com / admin123")
        print(f"User:  user@example.com / user123")

    except Exception as e:
        print(f"Seeding failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
