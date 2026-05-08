import sys
import os
from sqlalchemy import create_engine, text

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from db.base import engine

def fix_user_id_type():
    print("Starting migration to fix user_id type in google_sheets...")
    
    commands = [
        # Drop Constraint if exists
        "ALTER TABLE google_sheets DROP CONSTRAINT IF EXISTS google_sheets_user_id_fkey;",
        
        # Change column type
        "ALTER TABLE google_sheets ALTER COLUMN user_id TYPE VARCHAR(50) USING user_id::text;",
        
        # Re-add constraint
        """
        ALTER TABLE google_sheets 
        ADD CONSTRAINT google_sheets_user_id_fkey 
        FOREIGN KEY (user_id) REFERENCES businesses(busi_user_id);
        """
    ]

    try:
        with engine.connect() as conn:
            for cmd in commands:
                print(f"Executing: {cmd[:50]}...")
                conn.execute(text(cmd))
                conn.commit()
            print("Migration completed successfully.")
            
    except Exception as e:
        print(f"Migration Failed: {e}")

if __name__ == "__main__":
    fix_user_id_type()
