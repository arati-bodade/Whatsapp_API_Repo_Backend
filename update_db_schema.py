import sys
import os

# Add the current directory to path so we can import internal modules
sys.path.append(os.getcwd())

from db.session import engine
from sqlalchemy import text

def update_schema():
    print("🚀 Starting database schema update...")
    try:
        with engine.begin() as conn:
            # 1. Add source_file_url column
            print("   🛠️ adding 'source_file_url' to 'campaigns' table...")
            conn.execute(text('ALTER TABLE campaigns ADD COLUMN IF NOT EXISTS source_file_url TEXT;'))
            
            # 2. Make sheet_id nullable if it was NOT NULL
            print("   🛠️ Making 'sheet_id' nullable...")
            conn.execute(text('ALTER TABLE campaigns ALTER COLUMN sheet_id DROP NOT NULL;'))
            
            print("✅ Database schema updated successfully!")
    except Exception as e:
        print(f"❌ Error updating schema: {e}")
        # If it's just 'already exists', we are fine

if __name__ == "__main__":
    update_schema()
