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
        print("Starting Final Reconciliation (Standard Model)...")
        
        # 1. Fix Business Users
        users = db.query(BusiUser).all()
        for u in users:
            # Usage
            actual_used = db.query(func.sum(MessageUsageCreditLog.credits_deducted)).filter(
                MessageUsageCreditLog.busi_user_id == str(u.busi_user_id),
                MessageUsageCreditLog.credits_deducted > 0,
                MessageUsageCreditLog.source != "distribution"
            ).scalar() or 0.0
            
            # Distribution
            total_allocated = db.query(func.sum(MessageUsageCreditLog.credits_deducted)).filter(
                MessageUsageCreditLog.busi_user_id == str(u.busi_user_id),
                MessageUsageCreditLog.credits_deducted < 0
            ).scalar() or 0.0
            total_allocated = abs(total_allocated)
            
            u.credits_used = actual_used
            u.credits_remaining = total_allocated - actual_used
            print(f"Updated BusiUser {u.name}: Used={u.credits_used}, Remaining={u.credits_remaining}")
        
        # 2. Fix Resellers
        resellers = db.query(Reseller).all()
        for r in resellers:
            # Own usage
            own_usage = db.query(func.sum(MessageUsageCreditLog.credits_deducted)).filter(
                MessageUsageCreditLog.busi_user_id == r.reseller_id,
                MessageUsageCreditLog.credits_deducted > 0,
                MessageUsageCreditLog.source != "distribution"
            ).scalar() or 0.0
            
            # Sub-user usage
            sub_users = db.query(BusiUser).filter(BusiUser.parent_reseller_id == r.reseller_id).all()
            total_sub_usage = 0.0
            sub_user_ids = []
            for su in sub_users:
                sid = str(su.busi_user_id)
                sub_user_ids.append(sid)
                su_usage = db.query(func.sum(MessageUsageCreditLog.credits_deducted)).filter(
                    MessageUsageCreditLog.busi_user_id == sid,
                    MessageUsageCreditLog.credits_deducted > 0,
                    MessageUsageCreditLog.source != "distribution"
                ).scalar() or 0.0
                total_sub_usage += float(su_usage)
            
            # Distribution
            total_distributed = 0.0
            if sub_user_ids:
                total_distributed_raw = db.query(func.sum(MessageUsageCreditLog.credits_deducted)).filter(
                    MessageUsageCreditLog.busi_user_id.in_(sub_user_ids),
                    MessageUsageCreditLog.source == "distribution"
                ).scalar() or 0.0
                total_distributed = abs(total_distributed_raw)
            
            r.used_credits = own_usage + total_sub_usage
            r.available_credits = float(r.total_credits) - total_distributed - own_usage
            print(f"Updated Reseller {r.name}: Used={r.used_credits}, Available={r.available_credits}")

        db.commit()
        print("SUCCESS: Final Reconciliation complete.")
            
    except Exception as e:
        db.rollback()
        import traceback
        print(f"ERROR: {e}")
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    reconcile()
