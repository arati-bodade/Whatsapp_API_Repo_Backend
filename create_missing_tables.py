#!/usr/bin/env python3

from sqlalchemy import create_engine, text
from db.base import engine, Base

# Import ALL models to ensure they're registered with Base.metadata
from models.busi_user import BusiUser
from models.reseller import Reseller
from models.device import Device
from models.message import Message
from models.google_sheet import GoogleSheet, GoogleSheetTriggerHistory

def create_all_missing_tables():
    """Create all missing tables"""
    
    try:
        print("Creating all missing tables...")
        
        # Create all tables from all imported models
        Base.metadata.create_all(bind=engine)
        
        print("✅ All tables created successfully!")
        
        # Verify tables were created
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print(f"\nTotal tables in database: {len(tables)}")
        
        # Check for our specific tables
        if 'google_sheet' in tables:
            print("✅ 'google_sheet' table created")
        else:
            print("❌ 'google_sheet' table still missing")
            
        if 'sheet_trigger_history' in tables:
            print("✅ 'sheet_trigger_history' table created")
        else:
            print("❌ 'sheet_trigger_history' table still missing")
            
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_all_missing_tables()
