import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db.session import SessionLocal
from models.admin import MasterAdmin
from core.security import verify_password, get_password_hash

def check_admin():
    db = SessionLocal()
    try:
        admins = db.query(MasterAdmin).all()
        print(f"Found {len(admins)} admins.")
        for admin in admins:
            print(f"ID: {admin.admin_id}, Username: {admin.username}, Email: {admin.email}")
            # Try a common password or the one the user might be using if I knew it
            # But I don't know it. I can try to reset it to something known.
            
    finally:
        db.close()

if __name__ == "__main__":
    check_admin()
