from db.session import get_db
from models.message import Message
from sqlalchemy import func

db = next(get_db())
count = db.query(func.count(Message.message_id)).scalar()
print(f"Total messages in 'messages' table: {count}")

if count > 0:
    latest = db.query(Message).order_by(Message.sent_at.desc()).limit(5).all()
    for m in latest:
        print(f"ID: {m.message_id}, User: {m.busi_user_id}, Status: {m.status}, Credits: {m.credits_used}, Time: {m.sent_at}")
