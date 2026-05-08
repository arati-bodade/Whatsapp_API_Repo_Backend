#!/usr/bin/env python3

from sqlalchemy import create_engine, text
from db.base import engine, Base
from models.google_sheet import GoogleSheet, SheetTriggerHistory

def create_google_sheets_tables():
    """Create the missing Google Sheets tables"""
    
    try:
        print("Creating Google Sheets tables...")
        
        # Create all tables from models
        Base.metadata.create_all(bind=engine, tables=[
            GoogleSheet.__table__,
            SheetTriggerHistory.__table__
        ])
        
        print("✅ Google Sheets tables created successfully!")
        
        # Verify tables were created
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if 'google_sheet' in tables:
            print("✅ 'google_sheet' table verified")
        else:
            print("❌ 'google_sheet' table still missing")
            
        if 'sheet_trigger_history' in tables:
            print("✅ 'sheet_trigger_history' table verified")
        else:
            print("❌ 'sheet_trigger_history' table still missing")
            
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_google_sheets_tables()
