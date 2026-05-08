import sys
import os
sys.path.append(os.getcwd())

from db.session import SessionLocal
from models.message_usage import MessageUsageCreditLog
from sqlalchemy import text

def check_usage_today():
    db = SessionLocal()
    try:
        res = db.execute(text("SELECT usage_id, busi_user_id, credits_deducted, timestamp FROM message_usage_credit_logs WHERE timestamp >= CURRENT_DATE")).fetchall()
        for row in res:
            print(f"Log: {row.usage_id}, User: {row.busi_user_id}, Credits: {row.credits_deducted}, Time: {row.timestamp}")
    finally:
        db.close()

if __name__ == "__main__":
    check_usage_today()
