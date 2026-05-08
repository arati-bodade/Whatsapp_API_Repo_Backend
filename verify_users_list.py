import sys
import os
from sqlalchemy import text

# Add the current directory to sys.path
sys.path.append(os.getcwd())

from db.session import SessionLocal
from models.busi_user import BusiUser
from models.reseller import Reseller
from models.admin import MasterAdmin

def list_users():
    db = SessionLocal()
    try:
        print("--- Master Admins ---")
        admins = db.query(MasterAdmin).all()
        for a in admins:
            print(f"ID: {a.admin_id}, Email: {a.email}, Username: {a.username}")
            
        print("\n--- Resellers ---")
        resellers = db.query(Reseller).all()
        for r in resellers:
            print(f"ID: {r.reseller_id}, Email: {r.email}, Name: {r.name}")
            
        print("\n--- Business Users ---")
        users = db.query(BusiUser).all()
        for u in users:
            print(f"ID: {u.busi_user_id}, Email: {u.email}, Username: {u.username}, Status: {u.status}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    list_users()
