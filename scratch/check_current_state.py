import sys
import os
sys.path.append(os.getcwd())

from db.session import SessionLocal
from models.busi_user import BusiUser
from models.message_usage import MessageUsageCreditLog
from sqlalchemy import func

def check_current_state(email):
    db = SessionLocal()
    try:
        user = db.query(BusiUser).filter(BusiUser.email == email).first()
        if not user:
            print(f"User {email} not found")
            return
        
        user_uuid = str(user.busi_user_id)
        print(f"User: {user.name}")
        print(f"Credits Remaining (Table): {user.credits_remaining}")
        print(f"Credits Allocated (Table): {user.credits_allocated}")
        
        # Real-time calc
        used = db.query(func.sum(MessageUsageCreditLog.credits_deducted)).filter(
            MessageUsageCreditLog.busi_user_id == user_uuid,
            MessageUsageCreditLog.credits_deducted > 0
        ).scalar() or 0
        
        print(f"Credits Used (Logs): {used}")
        print(f"Real Remaining: {user.credits_allocated - used}")
        
    finally:
        db.close()

if __name__ == "__main__":
    check_current_state('sushant.bodade@gmail.com')
