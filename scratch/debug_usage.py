import sys
import os
sys.path.append(os.getcwd())

from db.session import SessionLocal
from models.busi_user import BusiUser
from models.message_usage import MessageUsageCreditLog
from models.credit_distribution import CreditDistribution
from sqlalchemy import func

def debug_credits(email):
    db = SessionLocal()
    try:
        user = db.query(BusiUser).filter(BusiUser.email == email).first()
        if not user:
            print(f"User {email} not found")
            return
        
        user_uuid = str(user.busi_user_id)
        print(f"User: {user.name} ({user_uuid})")
        print(f"Table credits_allocated: {user.credits_allocated}")
        print(f"Table credits_remaining: {user.credits_remaining}")
        
        # Credit Distributions
        dist_total = db.query(func.sum(CreditDistribution.credits_shared)).filter(
            CreditDistribution.to_business_user_id == user_uuid
        ).scalar() or 0
        print(f"Distributions Total: {dist_total}")
        
        # Usage Logs
        usage_total = db.query(func.sum(MessageUsageCreditLog.credits_deducted)).filter(
            MessageUsageCreditLog.busi_user_id == user_uuid,
            MessageUsageCreditLog.credits_deducted > 0
        ).scalar() or 0
        print(f"Usage Logs Total: {usage_total}")
        
        usage_count = db.query(MessageUsageCreditLog).filter(
            MessageUsageCreditLog.busi_user_id == user_uuid,
            MessageUsageCreditLog.credits_deducted > 0
        ).count()
        print(f"Usage Logs Count: {usage_count}")
        
        # Recent logs
        recent_logs = db.query(MessageUsageCreditLog).filter(
            MessageUsageCreditLog.busi_user_id == user_uuid
        ).order_by(MessageUsageCreditLog.timestamp.desc()).limit(5).all()
        
        print("\nRecent Logs:")
        for log in recent_logs:
            print(f"ID: {log.usage_id}, Deducted: {log.credits_deducted}, Bal After: {log.balance_after}, Source: {log.source}, Time: {log.timestamp}")

    finally:
        db.close()

if __name__ == "__main__":
    debug_credits('sushant.bodade@gmail.com')
