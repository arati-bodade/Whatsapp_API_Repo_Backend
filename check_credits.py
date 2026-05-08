import sys
import os

# Add root path to sys.path
sys.path.append(r"e:\whatsapp_platform_api\wh-api-backend-vikas")

from db.session import SessionLocal
from models.message_usage import MessageUsageCreditLog
from models.busi_user import BusiUser
from models.reseller import Reseller
from sqlalchemy import desc

def verify():
    db = SessionLocal()
    try:
        print("--- LAST 10 CREDIT LOGS ---")
        logs = db.query(MessageUsageCreditLog).order_by(desc(MessageUsageCreditLog.timestamp)).limit(10).all()
        for log in logs:
            print(f"ID: {log.usage_id} | User: {log.busi_user_id} | Credits: {log.credits_deducted} | Balance: {log.balance_after} | Time: {log.timestamp}")
            
        print("\n--- BUSINESS USERS BALANCE ---")
        users = db.query(BusiUser).all()
        for u in users:
            print(f"User: {u.username} ({u.busi_user_id}) | Credits: {u.credits_remaining} | Used: {u.credits_used}")
            
        print("\n--- RESELLERS BALANCE ---")
        resellers = db.query(Reseller).all()
        for r in resellers:
             print(f"Reseller: {r.username} ({r.reseller_id}) | Available: {r.available_credits}")
            
    finally:
        db.close()

if __name__ == "__main__":
    verify()
