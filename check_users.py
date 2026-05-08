"""
Quick script to check if users exist in the database.
"""

import sys
import os

# Add the parent directory to the path to import from the backend
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db.session import SessionLocal
from models.busi_user import BusiUser
from models.reseller import Reseller

def check_users():
    """Check if users exist in the database."""
    db = SessionLocal()
    
    try:
        # Check for "Srushti Lunge"
        print("=== Checking for 'Srushti Lunge' ===")
        busi_users = db.query(BusiUser).filter(
            (BusiUser.name.ilike("%srushti%")) |
            (BusiUser.business_name.ilike("%srushti%"))
        ).all()
        
        print(f"Found {len(busi_users)} BusiUsers matching 'Srushti':")
        for user in busi_users:
            print(f"  - Name: {user.name}, Business Name: {user.business_name}, Email: {user.email}, ID: {user.busi_user_id}")
        
        resellers = db.query(Reseller).filter(
            Reseller.name.ilike("%srushti%")
        ).all()
        
        print(f"Found {len(resellers)} Resellers matching 'Srushti':")
        for reseller in resellers:
            print(f"  - Name: {reseller.name}, Email: {reseller.email}, ID: {reseller.reseller_id}")
        
        # Check for "Om Lunge"
        print("\n=== Checking for 'Om Lunge' ===")
        busi_users = db.query(BusiUser).filter(
            (BusiUser.name.ilike("%om%")) |
            (BusiUser.business_name.ilike("%om%"))
        ).all()
        
        print(f"Found {len(busi_users)} BusiUsers matching 'Om':")
        for user in busi_users:
            print(f"  - Name: {user.name}, Business Name: {user.business_name}, Email: {user.email}, ID: {user.busi_user_id}")
        
        resellers = db.query(Reseller).filter(
            Reseller.name.ilike("%om%")
        ).all()
        
        print(f"Found {len(resellers)} Resellers matching 'Om':")
        for reseller in resellers:
            print(f"  - Name: {reseller.name}, Email: {reseller.email}, ID: {reseller.reseller_id}")
        
        # Check for "Mrunal Beauty"
        print("\n=== Checking for 'Mrunal Beauty' ===")
        busi_users = db.query(BusiUser).filter(
            (BusiUser.name.ilike("%mrunal%")) |
            (BusiUser.business_name.ilike("%mrunal%"))
        ).all()
        
        print(f"Found {len(busi_users)} BusiUsers matching 'Mrunal':")
        for user in busi_users:
            print(f"  - Name: {user.name}, Business Name: {user.business_name}, Email: {user.email}, ID: {user.busi_user_id}")
        
        resellers = db.query(Reseller).filter(
            Reseller.name.ilike("%mrunal%")
        ).all()
        
        print(f"Found {len(resellers)} Resellers matching 'Mrunal':")
        for reseller in resellers:
            print(f"  - Name: {reseller.name}, Email: {reseller.email}, ID: {reseller.reseller_id}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_users()
