
import asyncio
from db.session import SessionLocal
from models.busi_user import BusiUser
from sqlalchemy.future import select

async def check_user():
    db = SessionLocal()
    try:
        user = db.query(BusiUser).filter(BusiUser.email == "amit.verma@testmail.com").first()
        if user:
            print(f"User found: {user.email}")
            print(f"Status: {user.status}")
            print(f"Role: {user.role}")
            print(f"Password hash: {user.password_hash[:10]}...")
        else:
            print("User not found")
            
        # List all users
        users = db.query(BusiUser).limit(5).all()
        print("\nFirst 5 users:")
        for u in users:
            print(f"- {u.email} ({u.status})")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(check_user())
