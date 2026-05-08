import sys
import os
sys.path.append(os.getcwd())

from db.session import SessionLocal
from services.reseller_analytics_service import ResellerAnalyticsService
import json

def check():
    db = SessionLocal()
    try:
        service = ResellerAnalyticsService(db)
        reseller_id = 'ba57b395-4e43-4e78-9690-710dcfe2cad2'
        dashboard = service.generate_reseller_dashboard(reseller_id)
        
        print("Backend Dashboard Response:")
        print(f"Total Credits: {dashboard.total_credits}")
        print(f"Used Credits: {dashboard.used_credits}")
        print(f"Remaining Credits: {dashboard.remaining_credits}")
        print(f"Messages Sent: {dashboard.messages_sent}")
            
    finally:
        db.close()

if __name__ == "__main__":
    check()
