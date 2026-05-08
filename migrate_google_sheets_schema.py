#!/usr/bin/env python3

from sqlalchemy import create_engine, text
from db.base import engine
import uuid

def migrate_google_sheets_schema():
    """Migrate google_sheets table to match SQLAlchemy model"""
    
    try:
        with engine.connect() as conn:
            print("Starting google_sheets schema migration...")
            
            # Check if table exists and get current schema
            result = conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'google_sheets' 
                ORDER BY ordinal_position
            """))
            current_columns = result.fetchall()
            print(f"Current columns: {[col[0] for col in current_columns]}")
            
            # Drop and recreate table with correct schema
            print("Dropping existing table...")
            conn.execute(text("DROP TABLE IF EXISTS sheet_trigger_history CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS google_sheets CASCADE"))
            conn.commit()
            
            # Create table with correct schema using SQLAlchemy
            from models.google_sheet import GoogleSheet, SheetTriggerHistory
            from db.base import Base
            
            print("Creating tables with correct schema...")
            Base.metadata.create_all(bind=engine, tables=[
                GoogleSheet.__table__,
                SheetTriggerHistory.__table__
            ])
            
            print("✅ Migration completed successfully!")
            
            # Verify new schema
            result = conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'google_sheets' 
                ORDER BY ordinal_position
            """))
            new_columns = result.fetchall()
            
            print("\nNew google_sheets table schema:")
            for col in new_columns:
                print(f"  {col[0]}: {col[1]}")
                
    except Exception as e:
        print(f"❌ Migration error: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    migrate_google_sheets_schema()
