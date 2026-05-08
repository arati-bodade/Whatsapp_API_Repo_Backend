import sys
sys.path.append('.')
from db.session import SessionLocal
from models.message_usage import MessageUsageCreditLog
from datetime import datetime, timedelta, date
from sqlalchemy import extract

db = SessionLocal()

# Check all real usage logs
all_logs = db.query(MessageUsageCreditLog).all()
print(f'Total usage logs: {len(all_logs)}')

# Check today's logs
today = date.today()
today_logs = db.query(MessageUsageCreditLog).filter(
    extract('day', MessageUsageCreditLog.timestamp) == today.day,
    extract('month', MessageUsageCreditLog.timestamp) == today.month,
    extract('year', MessageUsageCreditLog.timestamp) == today.year
).all()

print(f'Today usage logs: {len(today_logs)}')

if today_logs:
    print('\nToday messages:')
    for i, log in enumerate(today_logs):
        sign = '+' if log.credits_deducted < 0 else ''
        msg_type = 'Payment' if log.credits_deducted < 0 else 'Message'
        time_str = log.timestamp.strftime('%H:%M')
        print(f'  {i+1}. {time_str} - {msg_type}: {log.message_id} ({sign}{log.credits_deducted} credits)')
else:
    print('No messages sent today')

# Check if there are any message sending logs (not payments)
message_logs = [log for log in all_logs if log.credits_deducted > 0]
print(f'\nMessage sending logs: {len(message_logs)}')

if message_logs:
    print('Recent messages:')
    for i, log in enumerate(message_logs[:5]):
        time_str = log.timestamp.strftime('%Y-%m-%d %H:%M')
        print(f'  {i+1}. {time_str} - {log.message_id} ({log.credits_deducted} credits)')

db.close()
