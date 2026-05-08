import sys
import os

# Add parent directory to sys.path to import from app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from db.base import SessionLocal
from models.busi_user import BusiUser
from models.reseller import Reseller
from models.message_usage import MessageUsageCreditLog

def fix_negative_credits():
    db = SessionLocal()
    try:
        print("Checking for negative credit balances...")
        
        # 1. Check BusiUser
        busi_users = db.query(BusiUser).filter(
            (BusiUser.credits_remaining < 0) | 
            (BusiUser.credits_used < 0) | 
            (BusiUser.credits_allocated < 0)
        ).all()
        
        if busi_users:
            print(f"Found {len(busi_users)} Business Users with negative values. Fixing...")
            for user in busi_users:
                if user.credits_remaining < 0:
                    print(f"  - User {user.email}: credits_remaining {user.credits_remaining} -> 0")
                    user.credits_remaining = 0
                if user.credits_used < 0:
                    print(f"  - User {user.email}: credits_used {user.credits_used} -> 0")
                    user.credits_used = 0
                if user.credits_allocated < 0:
                    print(f"  - User {user.email}: credits_allocated {user.credits_allocated} -> 0")
                    user.credits_allocated = 0
        
        # 2. Check Reseller
        resellers = db.query(Reseller).filter(
            (Reseller.available_credits < 0) | 
            (Reseller.used_credits < 0) | 
            (Reseller.total_credits < 0)
        ).all()
        
        if resellers:
            print(f"Found {len(resellers)} Resellers with negative values. Fixing...")
            for reseller in resellers:
                if reseller.available_credits < 0:
                    print(f"  - Reseller {reseller.email}: available_credits {reseller.available_credits} -> 0")
                    reseller.available_credits = 0
                if reseller.used_credits < 0:
                    print(f"  - Reseller {reseller.email}: used_credits {reseller.used_credits} -> 0")
                    reseller.used_credits = 0
                if reseller.total_credits < 0:
                    print(f"  - Reseller {reseller.email}: total_credits {reseller.total_credits} -> 0")
                    reseller.total_credits = 0
        
        # 3. Check MessageUsageCreditLog
        logs = db.query(MessageUsageCreditLog).filter(MessageUsageCreditLog.balance_after < 0).all()
        if logs:
            print(f"Found {len(logs)} Usage Logs with negative balance_after. Fixing...")
            for log in logs:
                print(f"  - Log {log.usage_id}: balance_after {log.balance_after} -> 0")
                log.balance_after = 0
        
        db.commit()
        print("Done! All negative values have been fixed.")
        
    except Exception as e:
        db.rollback()
        print(f"Error occurred: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    fix_negative_credits()
