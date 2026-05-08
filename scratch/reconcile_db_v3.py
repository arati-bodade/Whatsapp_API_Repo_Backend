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
        print("Starting Reconciliation (Single Deduction Model)...")
        
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
        
        # 2. Fix Resellers
        resellers = db.query(Reseller).all()
        for r in resellers:
            # Own usage
            own_usage = db.query(func.sum(MessageUsageCreditLog.credits_deducted)).filter(
                MessageUsageCreditLog.busi_user_id == r.reseller_id,
                MessageUsageCreditLog.credits_deducted > 0,
                MessageUsageCreditLog.source != "distribution"
            ).scalar() or 0.0
            
            # Sub-user usage (For aggregate counter only)
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
            
            total_aggregate_usage = own_usage + total_sub_usage
            
            # Update used_credits (Aggregate)
            if float(r.used_credits or 0) != float(total_aggregate_usage):
                print(f"Updating Reseller {r.name} Used: {r.used_credits} -> {total_aggregate_usage}")
                r.used_credits = total_aggregate_usage
            
            # Distribution
            total_distributed = 0.0
            if sub_user_ids:
                total_distributed_raw = db.query(func.sum(MessageUsageCreditLog.credits_deducted)).filter(
                    MessageUsageCreditLog.busi_user_id.in_(sub_user_ids),
                    MessageUsageCreditLog.source == "distribution"
                ).scalar() or 0.0
                total_distributed = abs(total_distributed_raw)
            
            # Correct Available = Total - Distributed - OwnUsage (ONLY)
            correct_available = float(r.total_credits) - total_distributed - own_usage
            
            if float(r.available_credits or 0) != float(correct_available):
                print(f"Updating Reseller {r.name} Available: {r.available_credits} -> {correct_available}")
                r.available_credits = correct_available

        db.commit()
        print("SUCCESS: Reconciliation complete.")
            
    except Exception as e:
        db.rollback()
        import traceback
        print(f"ERROR: {e}")
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    reconcile()
