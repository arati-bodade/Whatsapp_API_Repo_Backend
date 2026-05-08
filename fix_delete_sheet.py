#!/usr/bin/env python3

"""
Fix for Google Sheet delete functionality
This script provides a safer delete implementation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from db.session import get_db
from core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_delete_sheet_safe():
    """Test safe deletion approach"""
    
    try:
        # Get database URL from settings
        database_url = settings.DATABASE_URL
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Test if we can query the google_sheets table
            result = conn.execute(text("SELECT COUNT(*) FROM google_sheets"))
            count = result.scalar()
            print(f"Total sheets in database: {count}")
            
            # Test if we can query the trigger tables
            result = conn.execute(text("SELECT COUNT(*) FROM google_sheet_triggers"))
            trigger_count = result.scalar()
            print(f"Total triggers in database: {trigger_count}")
            
            result = conn.execute(text("SELECT COUNT(*) FROM sheet_trigger_history"))
            history_count = result.scalar()
            print(f"Total trigger history in database: {history_count}")
            
            # Show table structures
            print("\nGoogle Sheets table structure:")
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'google_sheets' 
                ORDER BY ordinal_position
            """))
            for row in result:
                print(f"  {row[0]}: {row[1]} ({'NULL' if row[2] == 'YES' else 'NOT NULL'})")
            
            print("\nTriggers table structure:")
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'google_sheet_triggers' 
                ORDER BY ordinal_position
            """))
            for row in result:
                print(f"  {row[0]}: {row[1]} ({'NULL' if row[2] == 'YES' else 'NOT NULL'})")
                
    except Exception as e:
        logger.error(f"Database error: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    test_delete_sheet_safe()
