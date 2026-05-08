import sys
sys.path.append('.')
from db.session import SessionLocal
from models.message_usage import MessageUsageCreditLog
from datetime import datetime

db = SessionLocal()

print('=== Checking Current Timestamps ===')

# Check message usage logs for Om Lunge
om_lunge_id = 'c83ca739-3e10-42ea-aaa0-be59640ce872'
logs = db.query(MessageUsageCreditLog).filter(
    MessageUsageCreditLog.busi_user_id == om_lunge_id
).order_by(MessageUsageCreditLog.timestamp.desc()).all()

print(f'Message logs for Om Lunge: {len(logs)}')

for i, log in enumerate(logs):
    print(f'{i+1}. {log.timestamp} - {log.message_id} ({log.credits_deducted:+d})')
    # Show what this looks like in JavaScript
    js_date = log.timestamp.isoformat()
    print(f'    ISO format: {js_date}')
    print(f'    Local time: {log.timestamp.strftime("%Y-%m-%d %H:%M:%S %Z")}')

db.close()
