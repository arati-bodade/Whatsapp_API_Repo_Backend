import sys
import os
sys.path.append(os.getcwd())

from db.session import SessionLocal
from models.busi_user import BusiUser
from models.message_usage import MessageUsageCreditLog
from sqlalchemy import extract, func
from datetime import datetime

def check_graph_data(email):
    db = SessionLocal()
    try:
        user = db.query(BusiUser).filter(BusiUser.email == email).first()
        if not user: return
        
        user_uuid = str(user.busi_user_id)
        current_year = datetime.now().year
        
        usage_rows = db.query(
            extract('month', MessageUsageCreditLog.timestamp).label('month'),
            func.count(MessageUsageCreditLog.usage_id).label('count')
        ).filter(
            MessageUsageCreditLog.busi_user_id == user_uuid,
            extract('year', MessageUsageCreditLog.timestamp) == current_year,
            MessageUsageCreditLog.credits_deducted > 0
        ).group_by(
            extract('month', MessageUsageCreditLog.timestamp)
        ).all()
        
        print(f"Graph Data for {email} ({current_year}):")
        for r in usage_rows:
            print(f"Month {int(r.month)}: {r.count} messages")
            
    finally:
        db.close()

if __name__ == "__main__":
    check_graph_data('sushant.bodade@gmail.com')
