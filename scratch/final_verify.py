from db.session import SessionLocal
from models.message_usage import MessageUsageCreditLog
from sqlalchemy import extract

db = SessionLocal()
user_id = '87624568-107c-43cc-ac83-a060f4395e9c'
current_year = 2026

# Check April (Month 4) with filter
apr_logs = db.query(MessageUsageCreditLog).filter(
    MessageUsageCreditLog.busi_user_id == user_id,
    extract('year', MessageUsageCreditLog.timestamp) == current_year,
    extract('month', MessageUsageCreditLog.timestamp) == 4,
    MessageUsageCreditLog.credits_deducted > 0
).all()
apr_total = sum(l.credits_deducted for l in apr_logs)

# Check May (Month 5) with filter
may_logs = db.query(MessageUsageCreditLog).filter(
    MessageUsageCreditLog.busi_user_id == user_id,
    extract('year', MessageUsageCreditLog.timestamp) == current_year,
    extract('month', MessageUsageCreditLog.timestamp) == 5,
    MessageUsageCreditLog.credits_deducted > 0
).all()
may_total = sum(l.credits_deducted for l in may_logs)

print(f"April Filtered Total: {apr_total}")
print(f"May Filtered Total: {may_total}")
print(f"Grand Total (Sent): {apr_total + may_total}")

db.close()
