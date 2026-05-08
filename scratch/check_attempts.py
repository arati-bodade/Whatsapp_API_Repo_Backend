import sys
import os
sys.path.append(os.getcwd())

from db.session import SessionLocal
from models.message import Message
from sqlalchemy import desc

def check_recent_attempts(email):
    db = SessionLocal()
    try:
        from models.busi_user import BusiUser
        user = db.query(BusiUser).filter(BusiUser.email == email).first()
        if not user:
            print("User not found")
            return
            
        print(f"Recent attempts for {user.name}:")
        attempts = db.query(Message).filter(Message.busi_user_id == user.busi_user_id).order_by(desc(Message.sent_at)).limit(10).all()
        
        for a in attempts:
            print(f"ID: {a.message_id}, To: {a.receiver_number}, Status: {a.status}, Time: {a.sent_at}")
            
    finally:
        db.close()

if __name__ == "__main__":
    check_recent_attempts('sushant.bodade@gmail.com')
