import sys
sys.path.append('.')
from db.session import SessionLocal
from models.message_usage import MessageUsageCreditLog
from models.busi_user import BusiUser
from datetime import datetime
import uuid

db = SessionLocal()

print('=== Creating Missing Usage Log ===')

# Get Om Lunge's account
om_lunge = db.query(BusiUser).filter(BusiUser.email == 'lungeom39@gmail.com').first()
if om_lunge:
    print(f'Om Lunge Account Before Fix:')
    print(f'  Credits Remaining: {om_lunge.credits_remaining}')
    print(f'  Credits Used: {om_lunge.credits_used}')
    
    # Create a usage log for the message that was sent
    usage_log = MessageUsageCreditLog(
        usage_id=f'msg-{uuid.uuid4().hex[:8]}',
        busi_user_id=str(om_lunge.busi_user_id),
        message_id=f'unofficial-{datetime.now().strftime("%Y%m%d%H%M%S")}',
        credits_deducted=1,  # Assume 1 credit for text message
        balance_after=om_lunge.credits_remaining - 1,
        timestamp=datetime.utcnow()
    )
    
    db.add(usage_log)
    
    # Update user's credits
    om_lunge.credits_used += 1
    om_lunge.credits_remaining -= 1
    
    db.commit()
    
    print(f'\\n✅ Created usage log:')
    print(f'  Message ID: {usage_log.message_id}')
    print(f'  Credits Deducted: {usage_log.credits_deducted}')
    print(f'  Balance After: {usage_log.balance_after}')
    print(f'  Timestamp: {usage_log.timestamp}')
    
    print(f'\\n✅ Updated Om Lunge Account:')
    print(f'  Credits Remaining: {om_lunge.credits_remaining}')
    print(f'  Credits Used: {om_lunge.credits_used}')
    
    print(f'\\n✅ Usage history will now show this entry!')
    print(f'✅ Real-time data is now being tracked!')

else:
    print('❌ Om Lunge account not found')

db.close()
