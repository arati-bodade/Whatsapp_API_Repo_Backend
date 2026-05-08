from db.session import SessionLocal
from models.busi_user import BusiUser
import uuid

def check_user(target_user_id):
    db = SessionLocal()
    try:
        # Check by busi_user_id (UUID)
        user = db.query(BusiUser).filter(BusiUser.busi_user_id == uuid.UUID(target_user_id)).first()
        if user:
            print(f"✅ User found: {user.name} ({user.email})")
            return
            
        print(f"❌ User NOT found by busi_user_id: {target_user_id}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_user("a6b02694-8e95-4c4e-9fce-841e7eb1b3f0")
