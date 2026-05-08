import sys
import os
sys.path.append(r"e:\whatsapp_platform_api\wh-api-backend-vikas")
from db.session import SessionLocal
from models.message_usage import MessageUsageCreditLog
from sqlalchemy import desc

def verify():
    db = SessionLocal()
    try:
        print("--- LAST 20 CREDIT LOGS ---")
        logs = db.query(MessageUsageCreditLog).order_by(desc(MessageUsageCreditLog.timestamp)).limit(20).all()
        for log in logs:
            print(f"ID: {log.usage_id} | User: {log.busi_user_id} | Credits: {log.credits_deducted} | Balance: {log.balance_after} | Time: {log.timestamp}")
    finally:
        db.close()

if __name__ == "__main__":
    verify()
