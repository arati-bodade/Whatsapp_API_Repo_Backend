import sys
import os
import asyncio
from datetime import datetime
import traceback
import uuid

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session
from db.base import SessionLocal, engine
from models.google_sheet import GoogleSheet
from models.busi_user import BusiUser

def test_manual_connect():
    db = SessionLocal()
    try:
        user_id = "e1593373-c78e-442f-bd52-34db818887b0"
        spreadsheet_id = "1xOY27h0MViQqlibeYhmMVqtNqgJMH_i6rMG233hJJ-M"
        
        print(f"Testing connection for Sheet: {spreadsheet_id}...")
        
        # Check if exists
        existing = db.query(GoogleSheet).filter(
            GoogleSheet.spreadsheet_id == spreadsheet_id,
            GoogleSheet.user_id == user_id
        ).first()
        
        if existing:
            print("Existing sheet found. Deleting...")
            db.delete(existing)
            db.commit()
            
        new_sheet = GoogleSheet(
            id=str(uuid.uuid4()),
            user_id=user_id,
            sheet_name="Test Sheet",
            spreadsheet_id=spreadsheet_id,
            worksheet_name="Sheet1",
            status="ACTIVE",
            total_rows=0,
            connected_at=datetime.utcnow(),
            trigger_enabled=False
        )
        db.add(new_sheet)
        db.commit()
        print(f"SUCCESS: Inserted Sheet ID: {new_sheet.id}")
        return True
        
    except Exception as e:
        print(f"ERROR: {str(e)[:400]}") # Print first 400 chars
        return False
    finally:
        db.close()

if __name__ == "__main__":
    if test_manual_connect():
        print("Done.")
