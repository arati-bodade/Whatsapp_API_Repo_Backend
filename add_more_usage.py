import sys
sys.path.append('.')
from db.session import SessionLocal
from models.message_usage import MessageUsageCreditLog
from datetime import datetime, timedelta
import uuid

db = SessionLocal()

# Add more diverse usage logs
additional_logs = [
    MessageUsageCreditLog(
        usage_id='msg-' + uuid.uuid4().hex[:8],
        busi_user_id='98dd8f19-2518-4ef7-b0ea-d0c303a9e99e',
        message_id='official-single-12345',
        credits_deducted=1,
        balance_after=332999,
        timestamp=datetime.now() - timedelta(hours=3)
    ),
    MessageUsageCreditLog(
        usage_id='msg-' + uuid.uuid4().hex[:8],
        busi_user_id='98dd8f19-2518-4ef7-b0ea-d0c303a9e99e',
        message_id='unofficial-bulk-67890',
        credits_deducted=5,
        balance_after=332994,
        timestamp=datetime.now() - timedelta(hours=2)
    ),
    MessageUsageCreditLog(
        usage_id='msg-' + uuid.uuid4().hex[:8],
        busi_user_id='98dd8f19-2518-4ef7-b0ea-d0c303a9e99e',
        message_id='google-trigger-11111',
        credits_deducted=2,
        balance_after=332992,
        timestamp=datetime.now() - timedelta(hours=1)
    ),
    MessageUsageCreditLog(
        usage_id='msg-' + uuid.uuid4().hex[:8],
        busi_user_id='98dd8f19-2518-4ef7-b0ea-d0c303a9e99e',
        message_id='bulk-group-99999',
        credits_deducted=10,
        balance_after=332982,
        timestamp=datetime.now() - timedelta(minutes=30)
    ),
    MessageUsageCreditLog(
        usage_id='msg-' + uuid.uuid4().hex[:8],
        busi_user_id='98dd8f19-2518-4ef7-b0ea-d0c303a9e99e',
        message_id='official-media-55555',
        credits_deducted=3,
        balance_after=332979,
        timestamp=datetime.now() - timedelta(minutes=15)
    )
]

for log in additional_logs:
    db.add(log)

db.commit()
print(f'✅ Added {len(additional_logs)} additional usage logs')

# Show all logs
all_logs = db.query(MessageUsageCreditLog).order_by(MessageUsageCreditLog.timestamp.desc()).all()
print(f'\nTotal usage logs: {len(all_logs)}')

print('\nRecent usage logs:')
for i, log in enumerate(all_logs[:6]):
    sign = '+' if log.credits_deducted < 0 else ''
    msg_type = 'Payment' if log.credits_deducted < 0 else 'Message'
    time_str = log.timestamp.strftime("%Y-%m-%d %H:%M")
    print(f'  {i+1}. {time_str} - {msg_type}: {log.message_id} ({sign}{log.credits_deducted} credits)')

db.close()
