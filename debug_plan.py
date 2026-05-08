from db.session import SessionLocal
from models.busi_user import BusiUser

db = SessionLocal()
user = db.query(BusiUser).first()
if user:
    print(f"User ID: {user.busi_user_id}")
    print(f"Plan ID: {user.plan_id}")
    print(f"Plan Name: {user.plan_name}")
    print(f"Credits: {user.credits_remaining}")
else:
    print("No users found.")
