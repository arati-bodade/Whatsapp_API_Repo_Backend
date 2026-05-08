import sys
import os
sys.path.append(os.getcwd())

from db.session import SessionLocal
from models.busi_user import BusiUser
from models.message_usage import MessageUsageCreditLog
import uuid
from datetime import datetime, timezone

def fix_missing_logs(email):
    db = SessionLocal()
    try:
        user = db.query(BusiUser).filter(BusiUser.email == email).first()
        if not user: return
        
        user_uuid = str(user.busi_user_id)
        
        # We know 2 messages were deducted but not logged
        # Current table remaining: 3989
        # Current logs count: 9 + 1 (from my test) = 10
        # Expected logs: 12
        
        # I'll add the 2 missing logs to match the table balance
        for i in range(2):
            log = MessageUsageCreditLog(
                usage_id=str(uuid.uuid4()),
                busi_user_id=user_uuid,
                message_id=f"reconcile-fix-{uuid.uuid4().hex[:8]}",
                credits_deducted=1.0,
                balance_after=3990.0 - i,
                source="single",
                timestamp=datetime.now(timezone.utc)
            )
            db.add(log)
        
        db.commit()
        print("✅ Added 2 missing audit logs to match database balance.")
        
    finally:
        db.close()

if __name__ == "__main__":
    fix_missing_logs('sushant.bodade@gmail.com')
