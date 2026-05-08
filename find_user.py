from db.session import SessionLocal
from models.busi_user import BusiUser
from models.google_sheet import GoogleSheet
import json

def find_user(email):
    db = SessionLocal()
    try:
        user = db.query(BusiUser).filter(BusiUser.email == email.lower().strip()).first()
        if user:
            print(json.dumps({
                "id": str(user.busi_user_id),
                "email": user.email,
                "name": user.name
            }, indent=2))
        else:
            print("User not found.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    find_user("amit.verma@testmail.com")
