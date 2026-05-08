import sys
import os
from sqlalchemy import create_engine, inspect

# Add the project root to sys.path
sys.path.append(r"d:\master admin dashboard 2 integration 30-3-2026\whatsapp-api-backend")

from core.config import settings

def check_db():
    try:
        engine = settings.engine
        inspector = inspect(engine)
        
        print("--- Database Tables ---")
        tables = inspector.get_table_names()
        for table in tables:
            print(f"Table: {table}")
            
        from sqlalchemy.orm import sessionmaker
        Session = sessionmaker(bind=engine)
        session = Session()
        
        from models.admin import MasterAdmin
        from models.reseller import Reseller
        from models.busi_user import BusiUser
        
        admin_count = session.query(MasterAdmin).count()
        reseller_count = session.query(Reseller).count()
        user_count = session.query(BusiUser).count()
        
        print(f"\n--- Row Counts ---")
        print(f"MasterAdmins: {admin_count}")
        print(f"Resellers: {reseller_count}")
        print(f"BusiUsers: {user_count}")
        
        if admin_count > 0:
            admin = session.query(MasterAdmin).first()
            print(f"\nExample Admin: {admin.email} (ID: {admin.admin_id})")
            
        session.close()
    except Exception as e:
        print(f"Error checking DB: {e}")

if __name__ == "__main__":
    check_db()
