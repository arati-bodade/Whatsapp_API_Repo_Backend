import sys
import os
sys.path.append(os.getcwd())

from db.session import SessionLocal
from models.busi_user import BusiUser
from core.security import get_password_hash

def reset_password():
    db = SessionLocal()
    try:
        user = db.query(BusiUser).filter(BusiUser.email == 'sushant.bodade@gmail.com').first()
        if user:
            new_password = "Sushant@123"
            user.password_hash = get_password_hash(new_password)
            db.commit()
            print(f"SUCCESS: Password for {user.email} has been reset to: {new_password}")
        else:
            print("ERROR: User not found.")
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    reset_password()
