import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the current directory to sys.path
sys.path.append(os.getcwd())

from core.config import settings
from db.session import get_db
from models.admin import MasterAdmin
from models.reseller import Reseller
from models.busi_user import BusiUser

def check():
    try:
        engine = settings.engine
        Session = sessionmaker(bind=engine)
        db = Session()
        
        print(f"Admins: {db.query(MasterAdmin).count()}")
        print(f"Resellers: {db.query(Reseller).count()}")
        print(f"Users: {db.query(BusiUser).count()}")
        
        db.close()
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    check()
