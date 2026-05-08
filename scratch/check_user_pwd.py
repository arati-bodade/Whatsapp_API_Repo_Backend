import sys
import os
sys.path.append(os.getcwd())

from db.session import SessionLocal
from models.busi_user import BusiUser

def check_user():
    db = SessionLocal()
    try:
        user = db.query(BusiUser).filter(BusiUser.email == 'sushant.bodade@gmail.com').first()
        if user:
            print(f"User Found: {user.name}")
            print(f"Email: {user.email}")
            print(f"Password Hash: {user.password_hash}")
            # Check if it looks like a hash (starts with $2b$)
            if user.password_hash.startswith('$2b$'):
                print("Status: Password is securely hashed.")
            else:
                print("Status: Password is plain text (Legacy).")
        else:
            print("User sushant.bodade@gmail.com not found.")
    finally:
        db.close()

if __name__ == "__main__":
    check_user()
