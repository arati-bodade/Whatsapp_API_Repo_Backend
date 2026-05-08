from db.session import SessionLocal
from models.message_usage import MessageUsageCreditLog
from sqlalchemy import extract

db = SessionLocal()
user_id = '87624568-107c-43cc-ac83-a060f4395e9c'

logs = db.query(MessageUsageCreditLog).filter(
    MessageUsageCreditLog.busi_user_id == user_id,
    extract('month', MessageUsageCreditLog.timestamp) == 4
).all()

for l in logs:
    print(f"ID: {l.usage_id}, TS: {l.timestamp}, Credits: {l.credits_deducted}, MsgID: {l.message_id}")

db.close()
