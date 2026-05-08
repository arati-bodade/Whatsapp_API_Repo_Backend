import sys
import os
sys.path.append(os.getcwd())

from db.session import SessionLocal
from models.message import Message
from sqlalchemy import func, extract
from datetime import datetime

def check_may_messages(email):
    db = SessionLocal()
    try:
        from models.busi_user import BusiUser
        user = db.query(BusiUser).filter(BusiUser.email == email).first()
        if not user:
            print(f"User {email} not found")
            return
        
        user_uuid = str(user.busi_user_id)
        current_year = datetime.now().year
        
        # Messages in May 2026
        may_count = db.query(Message).filter(
            Message.busi_user_id == user_uuid,
            extract('year', Message.sent_at) == current_year,
            extract('month', Message.sent_at) == 5
        ).count()
        
        print(f"Messages in May 2026 for {user.name}: {may_count}")
        
        # Last 5 messages overall
        last_msgs = db.query(Message).filter(Message.busi_user_id == user_uuid).order_by(Message.sent_at.desc()).limit(5).all()
        print("\nLast 5 Messages:")
        for m in last_msgs:
            print(f"ID: {m.message_id}, Time: {m.sent_at}, Status: {m.status}")

    finally:
        db.close()

if __name__ == "__main__":
    check_may_messages('sushant.bodade@gmail.com')
