import sys
sys.path.append('.')
from db.session import SessionLocal
from models.message_usage import MessageUsageCreditLog
from datetime import datetime

db = SessionLocal()

# Check current usage logs with timestamps
logs = db.query(MessageUsageCreditLog).all()
print(f'Total usage logs: {len(logs)}')

if logs:
    print('\nCurrent usage logs with timestamps:')
    for i, log in enumerate(logs[:5]):
        print(f'  {i+1}. {log.timestamp} - {log.message_id} ({log.credits_deducted:+d} credits)')
        print(f'     Formatted: {log.timestamp.strftime("%Y-%m-%d %H:%M:%S")}')
        
    # Check if timestamps look realistic
    now = datetime.now()
    for log in logs:
        time_diff = now - log.timestamp
        print(f'  Time difference: {time_diff}')
        if time_diff.total_seconds() < 0:
            print(f'  ❌ FUTURE TIMESTAMP: {log.timestamp}')
        elif time_diff.total_seconds() > 86400:  # More than 1 day old
            print(f'  ⚠️  OLD TIMESTAMP: {log.timestamp}')
        else:
            print(f'  ✅ RECENT TIMESTAMP: {log.timestamp}')

db.close()
