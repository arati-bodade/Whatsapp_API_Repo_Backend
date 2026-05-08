#!/usr/bin/env python3

from sqlalchemy import inspect, text
from db.base import engine, get_db
from models.google_sheet import GoogleSheet
from models.busi_user import BusiUser

def check_database_tables():
    """Check what tables exist in the database"""
    
    try:
        # Create inspector
        inspector = inspect(engine)
        
        # Get all table names
        tables = inspector.get_table_names()
        
        print("Existing tables in database:")
        for table in sorted(tables):
            print(f"  - {table}")
        
        # Check specifically for google_sheet table
        if 'google_sheet' in tables:
            print("\n✅ 'google_sheet' table exists")
            
            # Check table structure
            columns = inspector.get_columns('google_sheet')
            print("\nColumns in 'google_sheet' table:")
            for column in columns:
                print(f"  - {column['name']}: {column['type']}")
                
        elif 'google_sheets' in tables:
            print("\n✅ 'google_sheets' table exists")
            
            # Check table structure
            columns = inspector.get_columns('google_sheets')
            print("\nColumns in 'google_sheets' table:")
            for column in columns:
                print(f"  - {column['name']}: {column['type']}")
        else:
            print("\n❌ Neither 'google_sheet' nor 'google_sheets' table exists!")
            
        # Check if businesses table exists
        if 'businesses' in tables:
            print("\n✅ 'businesses' table exists")
        else:
            print("\n❌ 'businesses' table does not exist!")
            
    except Exception as e:
        print(f"❌ Error checking database: {e}")

if __name__ == "__main__":
    check_database_tables()
