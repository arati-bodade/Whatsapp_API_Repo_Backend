from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.google_sheet import GoogleSheet, SheetStatus
from core.config import settings
import uuid
from datetime import datetime

# Database setup
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

def verify_fix():
    print("--- Verifying Enum Fix ---")
    
    # Create test data
    test_user_id = "13e4566d-1478-4a94-8149-8c0813952731"  # Need a valid user ID, will try to fetch one
    
    # Fetch a valid user ID
    try:
        from models.busi_user import BusiUser
        user = db.query(BusiUser).first()
        if user:
            test_user_id = user.busi_user_id
            print(f"Using user_id: {test_user_id}")
        else:
            print("No users found in DB. Cannot proceed.")
            return
    except Exception as e:
        print(f"Error fetching user: {e}")
        return

    # Create a new Google Sheet record
    new_sheet = GoogleSheet(
        user_id=test_user_id,
        sheet_name="Test Enum Fix Sheet",
        spreadsheet_id="test_spreadsheet_id_" + str(uuid.uuid4()),
        status=SheetStatus.ACTIVE  # This should now work and send 'ACTIVE' to DB
    )
    
    try:
        db.add(new_sheet)
        db.commit()
        db.refresh(new_sheet)
        print(f"Successfully inserted sheet with ID: {new_sheet.id}")
        print(f"Sheet status: {new_sheet.status}")
        
        # Verify clean up
        db.delete(new_sheet)
        db.commit()
        print("Cleaned up test record.")
        
    except Exception as e:
        db.rollback()
        print(f"FAILED to insert sheet: {e}")

if __name__ == "__main__":
    verify_fix()
