from db.session import SessionLocal
from models.message_usage import MessageUsageCreditLog
from sqlalchemy import extract
from datetime import datetime

db = SessionLocal()
user_id = '87624568-107c-43cc-ac83-a060f4395e9c'
current_year = 2026

# Check April (Month 4)
apr_logs = db.query(MessageUsageCreditLog).filter(
    MessageUsageCreditLog.busi_user_id == user_id,
    extract('year', MessageUsageCreditLog.timestamp) == current_year,
    extract('month', MessageUsageCreditLog.timestamp) == 4
).all()

apr_total = sum(l.credits_deducted for l in apr_logs)

# Check May (Month 5)
may_logs = db.query(MessageUsageCreditLog).filter(
    MessageUsageCreditLog.busi_user_id == user_id,
    extract('year', MessageUsageCreditLog.timestamp) == current_year,
    extract('month', MessageUsageCreditLog.timestamp) == 5
).all()

may_total = sum(l.credits_deducted for l in may_logs)

print(f"User: {user_id}")
print(f"April Total Credits: {apr_total} (Logs count: {len(apr_logs)})")
print(f"May Total Credits: {may_total} (Logs count: {len(may_logs)})")

db.close()
