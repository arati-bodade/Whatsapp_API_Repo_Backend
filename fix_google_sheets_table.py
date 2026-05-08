#!/usr/bin/env python3

from sqlalchemy import create_engine, text
from db.base import engine, Base
from models.google_sheet import GoogleSheet, SheetTriggerHistory

def fix_google_sheets_table():
    """Drop and recreate google_sheets table with correct schema"""
    
    try:
        with engine.connect() as conn:
            # Drop existing tables if they exist
            print("Dropping existing google_sheets tables...")
            
            # Drop in correct order to handle foreign key constraints
            conn.execute(text("DROP TABLE IF EXISTS sheet_trigger_history CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS google_sheets CASCADE"))
            
            conn.commit()
            print("✅ Old tables dropped")
            
            # Verify tables are gone
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('google_sheets', 'sheet_trigger_history')
            """))
            remaining = result.fetchall()
            
            if remaining:
                print(f"❌ Tables still exist: {[r[0] for r in remaining]}")
                return
            else:
                print("✅ Tables successfully dropped")
            
        # Create tables using SQLAlchemy models
        print("Creating tables with correct schema...")
        Base.metadata.create_all(bind=engine, tables=[
            GoogleSheet.__table__,
            SheetTriggerHistory.__table__
        ])
        
        print("✅ Google Sheets tables recreated with correct schema!")
        
        # Verify the new schema
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'google_sheets' 
                ORDER BY ordinal_position
            """))
            columns = result.fetchall()
            
            print('\nNew google_sheets table schema:')
            for col in columns:
                print(f'  {col[0]}: {col[1]}')
                
    except Exception as e:
        print(f"❌ Error fixing tables: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_google_sheets_table()
