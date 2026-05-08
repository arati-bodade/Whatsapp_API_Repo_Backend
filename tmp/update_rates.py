import os
import sys
from sqlalchemy.orm import Session
from datetime import datetime

# Add current directory to path
sys.path.append(os.getcwd())

from db.session import SessionLocal
from models.busi_user import BusiUser
from models.plan import Plan

def sync_rates():
    db = SessionLocal()
    try:
        users = db.query(BusiUser).filter(BusiUser.plan_id != None).all()
        updated = 0
        print(f"Checking {len(users)} users with plans...")
        
        for u in users:
            plan = db.query(Plan).filter(Plan.plan_id == u.plan_id).first()
            if plan:
                # If rate is 0 or 1, and plan has a different rate (like 0.25)
                if u.consumption_rate != plan.deduction_value:
                    print(f"Syncing {u.email}: {u.consumption_rate} -> {plan.deduction_value}")
                    u.consumption_rate = plan.deduction_value
                    updated += 1
        
        db.commit()
        print(f"Done. Updated {updated} users.")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    sync_rates()
