import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db.session import SessionLocal
from models.admin import MasterAdmin
from core.security import get_password_hash

def reset_admin_password():
    db = SessionLocal()
    try:
        admin = db.query(MasterAdmin).filter(MasterAdmin.email == "adminlogin6631@gmail.com").first()
        if not admin:
            print("Admin not found!")
            return
        
        new_password = "Admin@123"
        admin.password_hash = get_password_hash(new_password)
        db.commit()
        print(f"Password reset successfully for {admin.email}")
        print(f"New password: {new_password}")
            
    finally:
        db.close()

if __name__ == "__main__":
    reset_admin_password()
