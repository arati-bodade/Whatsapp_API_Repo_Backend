import sys
sys.path.append('.')
from db.session import SessionLocal
from models.message_usage import MessageUsageCreditLog
from datetime import datetime, timedelta
import uuid

db = SessionLocal()

# Get current time
now = datetime.now()
print(f'Current time: {now.strftime("%Y-%m-%d %H:%M:%S")}')

# Clear existing logs
logs = db.query(MessageUsageCreditLog).all()
for log in logs:
    db.delete(log)
db.commit()

# Create realistic message logs for today with unique IDs
realistic_logs = [
    {
        'usage_id': f'msg-{uuid.uuid4().hex[:8]}',
        'busi_user_id': 'a4ea62f8-b476-4c80-810b-f8f681029944',
        'message_id': 'official-single-test-001',
        'credits_deducted': 1,
        'balance_after': 4990,
        'timestamp': now - timedelta(hours=8)  # 8 hours ago
    },
    {
        'usage_id': f'msg-{uuid.uuid4().hex[:8]}',
        'busi_user_id': 'a4ea62f8-b476-4c80-810b-f8f681029944',
        'message_id': 'unofficial-bulk-test-002',
        'credits_deducted': 5,
        'balance_after': 4985,
        'timestamp': now - timedelta(hours=6)  # 6 hours ago
    },
    {
        'usage_id': f'msg-{uuid.uuid4().hex[:8]}',
        'busi_user_id': 'a4ea62f8-b476-4c80-810b-f8f681029944',
        'message_id': 'google-trigger-test-003',
        'credits_deducted': 2,
        'balance_after': 4983,
        'timestamp': now - timedelta(hours=4)  # 4 hours ago
    },
    {
        'usage_id': f'msg-{uuid.uuid4().hex[:8]}',
        'busi_user_id': 'a4ea62f8-b476-4c80-810b-f8f681029944',
        'message_id': 'bulk-group-test-004',
        'credits_deducted': 10,
        'balance_after': 4973,
        'timestamp': now - timedelta(hours=2)  # 2 hours ago
    },
    {
        'usage_id': f'msg-{uuid.uuid4().hex[:8]}',
        'busi_user_id': 'a4ea62f8-b476-4c80-810b-f8f681029944',
        'message_id': 'official-media-test-005',
        'credits_deducted': 3,
        'balance_after': 4970,
        'timestamp': now - timedelta(hours=1)  # 1 hour ago
    }
]

for log_data in realistic_logs:
    new_log = MessageUsageCreditLog(**log_data)
    db.add(new_log)

db.commit()
print(f'✅ Created {len(realistic_logs)} realistic message logs for today')

# Show the new logs
new_logs = db.query(MessageUsageCreditLog).all()
for i, log in enumerate(new_logs):
    print(f'  {i+1}. {log.timestamp.strftime("%Y-%m-%d %H:%M")} - {log.message_id} ({log.credits_deducted:+d} credits)')

db.close()
