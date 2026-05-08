from db.session import SessionLocal
from models.reseller import Reseller
from models.reseller_analytics import ResellerAnalytics
import uuid

def create_analytics():
    db = SessionLocal()
    email = "rohit.mehta@example.com"
    
    reseller = db.query(Reseller).filter(Reseller.email == email).first()
    if not reseller:
        print("Reseller not found!")
        return

    existing = db.query(ResellerAnalytics).filter(ResellerAnalytics.reseller_id == reseller.reseller_id).first()
    if existing:
        print("Analytics already exist.")
    else:
        print(f"Creating analytics for {email}...")
        analytics = ResellerAnalytics(
            reseller_id=reseller.reseller_id,
            total_credits_purchased=1000,
            total_credits_distributed=0,
            remaining_credits=1000,
            business_user_stats=[],
            reseller=reseller
        )
        db.add(analytics)
        db.commit()
        print("Analytics created successfully.")
    db.close()

if __name__ == "__main__":
    create_analytics()
