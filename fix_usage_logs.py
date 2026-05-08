import sys
sys.path.append('.')
from db.session import SessionLocal
from models.message_usage import MessageUsageCreditLog
from models.busi_user import BusiUser
from datetime import datetime, timedelta
import uuid

db = SessionLocal()

# Get the correct user ID
user = db.query(BusiUser).filter(BusiUser.busi_user_id == 'a4ea62f8-b476-4c80-810b-f8f681029944').first()

if user:
    print(f'Found user: {user.busi_user_id} with {user.credits_remaining} credits')
    
    # Delete old usage logs
    old_logs = db.query(MessageUsageCreditLog).all()
    for log in old_logs:
        db.delete(log)
    db.commit()
    print(f'Deleted {len(old_logs)} old usage logs')
    
    # Create new usage logs with correct user ID and proper balance tracking
    new_logs = [
        MessageUsageCreditLog(
            usage_id='msg-' + uuid.uuid4().hex[:8],
            busi_user_id=user.busi_user_id,
            message_id='official-single-12345',
            credits_deducted=1,
            balance_after=3998,
            timestamp=datetime.now() - timedelta(hours=4)
        ),
        MessageUsageCreditLog(
            usage_id='msg-' + uuid.uuid4().hex[:8],
            busi_user_id=user.busi_user_id,
            message_id='unofficial-bulk-67890',
            credits_deducted=5,
            balance_after=3993,
            timestamp=datetime.now() - timedelta(hours=3)
        ),
        MessageUsageCreditLog(
            usage_id='msg-' + uuid.uuid4().hex[:8],
            busi_user_id=user.busi_user_id,
            message_id='google-trigger-11111',
            credits_deducted=2,
            balance_after=3991,
            timestamp=datetime.now() - timedelta(hours=2)
        ),
        MessageUsageCreditLog(
            usage_id='msg-' + uuid.uuid4().hex[:8],
            busi_user_id=user.busi_user_id,
            message_id='bulk-group-99999',
            credits_deducted=10,
            balance_after=3981,
            timestamp=datetime.now() - timedelta(hours=1)
        ),
        MessageUsageCreditLog(
            usage_id='msg-' + uuid.uuid4().hex[:8],
            busi_user_id=user.busi_user_id,
            message_id='official-media-55555',
            credits_deducted=3,
            balance_after=3978,
            timestamp=datetime.now() - timedelta(minutes=30)
        ),
        MessageUsageCreditLog(
            usage_id='purchase-' + uuid.uuid4().hex[:8],
            busi_user_id=user.busi_user_id,
            message_id='PLAN-STARTER',
            credits_deducted=-25000,  # Negative = Added
            balance_after=28978,
            timestamp=datetime.now() - timedelta(days=1)
        )
    ]
    
    for log in new_logs:
        db.add(log)
    
    db.commit()
    print(f'✅ Created {len(new_logs)} new usage logs for user {user.busi_user_id}')
    
    # Update user balance to match latest log
    user.credits_remaining = 3978
    db.commit()
    print(f'✅ Updated user balance to: {user.credits_remaining}')
    
    # Show the logs
    all_logs = db.query(MessageUsageCreditLog).filter(MessageUsageCreditLog.busi_user_id == user.busi_user_id).order_by(MessageUsageCreditLog.timestamp.desc()).all()
    print(f'\nUser usage logs ({len(all_logs)}):')
    for i, log in enumerate(all_logs):
        sign = '+' if log.credits_deducted < 0 else ''
        msg_type = 'Payment' if log.credits_deducted < 0 else 'Message'
        time_str = log.timestamp.strftime("%Y-%m-%d %H:%M")
        print(f'  {i+1}. {time_str} - {msg_type}: {log.message_id} ({sign}{log.credits_deducted} credits, balance: {log.balance_after})')

else:
    print('User not found')

db.close()
