import sys
import os
from sqlalchemy.orm import sessionmaker

# Add the project root to sys.path
sys.path.append(r"d:\master admin dashboard 2 integration 30-3-2026\whatsapp-api-backend")

from core.config import settings
from models.reseller import Reseller

def get_reseller_plan(email):
    try:
        engine = settings.engine
        Session = sessionmaker(bind=engine)
        session = Session()
        
        reseller = session.query(Reseller).filter(Reseller.email == email).first()
        
        if reseller:
            print(f"Reseller Found: {reseller.name}")
            print(f"Email: {reseller.email}")
            print(f"Current Plan: {reseller.plan_name if reseller.plan_name else 'No plan'}")
            print(f"Plan ID: {reseller.plan_id}")
            print(f"Plan Expiry: {reseller.plan_expiry}")
            print(f"Wallet - Total: {reseller.total_credits}, Available: {reseller.available_credits}")
        else:
            print(f"No reseller found with email: {email}")
            
        session.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_reseller_plan("vikaskambale6631@gmail.com")
