from db.session import SessionLocal
from models.message_usage import MessageUsageCreditLog
from sqlalchemy import extract
from datetime import datetime

db = SessionLocal()
user_id = '87624568-107c-43cc-ac83-a060f4395e9c'
current_year = 2026

logs = db.query(MessageUsageCreditLog).filter(
    MessageUsageCreditLog.busi_user_id == user_id,
    extract('year', MessageUsageCreditLog.timestamp) == current_year,
    extract('month', MessageUsageCreditLog.timestamp) == 5
).all()

print(f"Total billing logs in May for user {user_id}: {len(logs)}")
for l in logs:
    print(f"ID: {l.usage_id}, TS: {l.timestamp}, Credits: {l.credits_deducted}, MsgID: {l.message_id}")

db.close()
