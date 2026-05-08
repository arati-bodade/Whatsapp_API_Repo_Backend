from db.session import get_db
from models.message_usage import MessageUsageCreditLog
from datetime import datetime
import uuid

db = next(get_db())
user_id = "a4ea62f8-b476-4c80-810b-f8f681029944" # Himanshu

# Check current balance
from models.busi_user import BusiUser
u = db.query(BusiUser).filter(BusiUser.busi_user_id == user_id).first()
if u:
    new_bal = u.credits_remaining - 1
    u.credits_remaining = new_bal
    u.credits_used += 1
    
    log = MessageUsageCreditLog(
        usage_id=f"test-{uuid.uuid4().hex[:8]}",
        busi_user_id=user_id,
        message_id="TEST-MSG-DEDUCTION",
        credits_deducted=1,
        balance_after=new_bal,
        timestamp=datetime.now()
    )
    db.add(log)
    db.commit()
    print(f"Simulated a 1 credit deduction for Himanshu. New bal: {new_bal}")
else:
    print("User not found.")
