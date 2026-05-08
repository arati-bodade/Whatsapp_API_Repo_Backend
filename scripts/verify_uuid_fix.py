import sys
import os
import uuid
import traceback
from sqlalchemy.orm import Session
from sqlalchemy import text

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from db.base import SessionLocal, engine
from models.google_sheet import GoogleSheet

def verify_uuid():
    print("Verifying UUID fix...")
    
    # 1. Inspect Schema Type via SQL
    print("\n--- Checking database column type ---")
    with engine.connect() as conn:
        result = conn.execute(text("SELECT data_type FROM information_schema.columns WHERE table_name='google_sheets' AND column_name='user_id'"))
        col_type = result.scalar()
        print(f"google_sheets.user_id type: {col_type}")
        
        if col_type != 'uuid':
            print("FAILURE: Column type is not 'uuid'")
            return False
            
    # 2. Test Insert with UUID object
    print("\n--- Testing Insert with UUID object ---")
    db = SessionLocal()
    try:
        # Generate random UUIDs
        test_id = uuid.uuid4()
        test_user_id = uuid.uuid4() # We assume a business user might not exist, might violate FK if we enforce it.
        # But we added constraints back. We must use a valid user_id if constraints are active.
        # Let's inspect ONE valid user_id from businesses first.
        
        valid_user_id = None
        user_res = db.execute(text("SELECT busi_user_id FROM businesses LIMIT 1"))
        row = user_res.first()
        if row:
            valid_user_id = row[0] # This should be a UUID object now if we mapped it, or string if raw SQL
        
        if not valid_user_id:
            print("WARNING: No business user found. Creating a fake one might fail FK.")
            valid_user_id = test_user_id
        else:
            print(f"Using existing user_id from DB: {valid_user_id} (Type: {type(valid_user_id)})")
            # If valid_user_id is string (from raw sql return), convert to UUID to test our model
            if isinstance(valid_user_id, str):
                valid_user_id = uuid.UUID(valid_user_id)

        new_sheet = GoogleSheet(
            id=test_id,
            user_id=valid_user_id, # Passing actual UUID object
            sheet_name="UUID Test Sheet",
            spreadsheet_id="123_uuid_test",
            worksheet_name="Sheet1"
        )
        db.add(new_sheet)
        db.commit()
        print(f"SUCCESS: Inserted GoogleSheet with UUID id={new_sheet.id} (Type: {type(new_sheet.id)})")
        
        # 3. Test Query
        print("\n--- Testing Query ---")
        fetched = db.query(GoogleSheet).filter(GoogleSheet.id == test_id).first()
        if fetched:
             print(f"SUCCESS: Fetched GoogleSheet. id={fetched.id} (Type: {type(fetched.id)})")
             
             # Clean up
             db.delete(fetched)
             db.commit()
             print("Cleaned up test record.")
             return True
        else:
            print("FAILURE: Could not fetch inserted record.")
            return False

    except Exception as e:
        print(f"FAILURE: {e}")
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    verify_uuid()
