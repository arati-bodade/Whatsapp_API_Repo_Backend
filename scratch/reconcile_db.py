import sys
import os
sys.path.append(os.getcwd())

from db.session import SessionLocal
from models.busi_user import BusiUser
from models.reseller import Reseller
from models.message_usage import MessageUsageCreditLog
from sqlalchemy import func

def reconcile():
    db = SessionLocal()
    try:
        print("Starting Database Reconciliation...")
        
        # 1. Fix Business Users
        users = db.query(BusiUser).all()
        for u in users:
            actual_used = db.query(func.sum(MessageUsageCreditLog.credits_deducted)).filter(
                MessageUsageCreditLog.busi_user_id == str(u.busi_user_id),
                MessageUsageCreditLog.credits_deducted > 0,
                MessageUsageCreditLog.source != "distribution"
            ).scalar() or 0.0
            
            if float(u.credits_used or 0) != float(actual_used):
                print(f"Updating BusiUser {u.name}: {u.credits_used} -> {actual_used}")
                u.credits_used = actual_used
        
        # 2. Fix Resellers (Sync with AGGREGATE of all sub-users + self)
        resellers = db.query(Reseller).all()
        for r in resellers:
            # Find all sub-users
            sub_user_ids = [str(uid[0]) for uid in db.query(BusiUser.busi_user_id).filter(BusiUser.parent_reseller_id == r.reseller_id).all()]
            all_involved_ids = sub_user_ids + [r.reseller_id]
            
            actual_used = db.query(func.sum(MessageUsageCreditLog.credits_deducted)).filter(
                MessageUsageCreditLog.busi_user_id.in_(all_involved_ids),
                MessageUsageCreditLog.credits_deducted > 0,
                MessageUsageCreditLog.source != "distribution"
            ).scalar() or 0.0
            
            if float(r.used_credits or 0) != float(actual_used):
                print(f"Updating Reseller {r.name}: {r.used_credits} -> {actual_used}")
                r.used_credits = actual_used

        db.commit()
        print("SUCCESS: Reconciliation complete.")
            
    except Exception as e:
        db.rollback()
        print(f"ERROR: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    reconcile()
