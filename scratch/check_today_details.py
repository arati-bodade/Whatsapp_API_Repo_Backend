import sys
import os
sys.path.append(os.getcwd())

from db.session import SessionLocal
from models.message import Message
from sqlalchemy import text

def check_today_details():
    db = SessionLocal()
    try:
        res = db.execute(text("SELECT message_id, busi_user_id, sent_at FROM messages WHERE sent_at >= CURRENT_DATE")).fetchall()
        for row in res:
            print(f"Msg: {row.message_id}, User: {row.busi_user_id}, Time: {row.sent_at}")
    finally:
        db.close()

if __name__ == "__main__":
    check_today_details()
