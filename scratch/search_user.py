import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db.session import SessionLocal
from models.reseller import Reseller
from models.busi_user import BusiUser
from models.admin import MasterAdmin

def search_user():
    db = SessionLocal()
    try:
        email = "adminlogin6631@gmail.com"
        print(f"Searching for {email} across all tables...")
        
        admin = db.query(MasterAdmin).filter(MasterAdmin.email == email).first()
        if admin: print(f"Found in MasterAdmin: {admin.admin_id}")
        
        reseller = db.query(Reseller).filter(Reseller.email == email).first()
        if reseller: print(f"Found in Reseller: {reseller.reseller_id}")
        
        user = db.query(BusiUser).filter(BusiUser.email == email).first()
        if user: print(f"Found in BusiUser: {user.busi_user_id}")
            
    finally:
        db.close()

if __name__ == "__main__":
    search_user()
