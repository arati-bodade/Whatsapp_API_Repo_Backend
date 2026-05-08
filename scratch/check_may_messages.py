from db.session import SessionLocal
from models.message import Message
from sqlalchemy import extract
from datetime import datetime

db = SessionLocal()
user_id = '87624568-107c-43cc-ac83-a060f4395e9c'
current_year = 2026

messages = db.query(Message).filter(
    Message.busi_user_id == user_id,
    extract('year', Message.sent_at) == current_year,
    extract('month', Message.sent_at) == 5
).all()

print(f"Total messages in May for user {user_id}: {len(messages)}")
for m in messages:
    print(f"ID: {m.message_id}, Sent At: {m.sent_at}, Status: {m.status}")

db.close()
