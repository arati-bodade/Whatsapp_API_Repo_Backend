
import sys
import os

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from db.base import SessionLocal

def fix_enums():
    db = SessionLocal()
    try:
        print("Updating device_type to uppercase...")
        # Direct SQL update to bypass SQLAlchemy Enum validation issues during fetch
        db.execute(text("UPDATE devices SET device_type = UPPER(device_type)"))
        db.commit()
        print("Successfully updated device_type values.")
    except Exception as e:
        print(f"Error updating DB: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_enums()
