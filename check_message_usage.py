import sys
sys.path.append('.')
from db.session import SessionLocal
from models.message_usage import MessageUsageCreditLog
from models.busi_user import BusiUser
from datetime import datetime, timedelta
import uuid

db = SessionLocal()

print('=== Checking Current Message Usage ===')

# Check Om Lunge's current status
om_lunge = db.query(BusiUser).filter(BusiUser.email == 'lungeom39@gmail.com').first()
if om_lunge:
    print(f'Om Lunge Current Status:')
    print(f'  Credits Remaining: {om_lunge.credits_remaining}')
    print(f'  Credits Allocated: {om_lunge.credits_allocated}')
    print(f'  Credits Used: {om_lunge.credits_used}')
    print(f'  User ID: {om_lunge.busi_user_id}')

# Check all current usage logs (busi_user_id is stored as string)
all_logs = db.query(MessageUsageCreditLog).filter(
    MessageUsageCreditLog.busi_user_id == str(om_lunge.busi_user_id)
).order_by(MessageUsageCreditLog.timestamp.desc()).all()

print(f'\nCurrent Usage Logs: {len(all_logs)}')
for i, log in enumerate(all_logs):
    print(f'  {i+1}. {log.timestamp} - {log.message_id} ({log.credits_deducted:+d}) - Balance: {log.balance_after}')

# Check if there are any recent message logs (last 1 hour)
recent_time = datetime.utcnow() - timedelta(hours=1)
recent_logs = db.query(MessageUsageCreditLog).filter(
    MessageUsageCreditLog.busi_user_id == str(om_lunge.busi_user_id),
    MessageUsageCreditLog.timestamp >= recent_time
).count()

print(f'\nRecent Usage (last 1 hour): {recent_logs}')

# Check for message logs in last 24 hours
day_ago = datetime.utcnow() - timedelta(hours=24)
day_logs = db.query(MessageUsageCreditLog).filter(
    MessageUsageCreditLog.busi_user_id == str(om_lunge.busi_user_id),
    MessageUsageCreditLog.timestamp >= day_ago
).count()

print(f'Usage (last 24 hours): {day_logs}')

# If no recent usage, check if credits were actually deducted
if om_lunge.credits_used > 0 and recent_logs == 0:
    print(f'\n⚠️  ISSUE: Credits used ({om_lunge.credits_used}) but no recent usage logs found!')
    print(f'   This suggests message usage is not being logged properly')

if om_lunge.credits_remaining < om_lunge.credits_allocated:
    print(f'\n✅ Credits have been used: {om_lunge.credits_allocated - om_lunge.credits_remaining}')
else:
    print(f'\nℹ️  No credits used recently')

db.close()
