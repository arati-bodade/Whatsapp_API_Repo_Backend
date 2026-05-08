import sys
import os
sys.path.append(os.getcwd())

from db.session import SessionLocal
from models.message import Message
from datetime import datetime, timezone

def check_today_all():
    db = SessionLocal()
    try:
        today = datetime.now(timezone.utc).date()
        count = db.query(Message).filter(func.cast(Message.sent_at, Date) == today).count()
        # Wait, using simple string check or similar if cast is tricky
        print(f"Total messages today: {count}")
    except Exception as e:
        # Fallback to direct query
        from sqlalchemy import text
        res = db.execute(text("SELECT count(*) FROM messages WHERE sent_at >= CURRENT_DATE")).scalar()
        print(f"Total messages today (SQL): {res}")
    finally:
        db.close()

if __name__ == "__main__":
    check_today_all()
