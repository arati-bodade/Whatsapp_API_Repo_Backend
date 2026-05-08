from db.session import SessionLocal
from models.user import User as PlatformUser
import uuid

def check_platform_user(target_user_id):
    db = SessionLocal()
    try:
        user = db.query(PlatformUser).filter(PlatformUser.id == uuid.UUID(target_user_id)).first()
        if user:
            print(f"✅ Platform User found: {user.name} ({user.email}), Role: {user.role}")
            return
            
        print(f"❌ Platform User NOT found by id: {target_user_id}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_platform_user("a6b02694-8e95-4c4e-9fce-841e7eb1b3f0")
