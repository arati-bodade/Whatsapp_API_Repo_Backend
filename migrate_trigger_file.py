import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def update_db_schema():
    print(f"Connecting to database to add source_file_url columns to triggers...")
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # 1. Add source_file_url to google_sheet_triggers
        try:
            # First, check if column exists
            cur.execute("ALTER TABLE google_sheet_triggers ADD COLUMN source_file_url TEXT;")
            print("- Added 'source_file_url' to 'google_sheet_triggers' table.")
        except Exception as e:
            if "already exists" in str(e):
                print("- 'source_file_url' already exists.")
            else:
                print(f"- Error: {e}")
            conn.rollback()
            cur = conn.cursor()
            
        # 2. Update sheet_id to be nullable (for file-only triggers)
        try:
            cur.execute("ALTER TABLE google_sheet_triggers ALTER COLUMN sheet_id DROP NOT NULL;")
            print("- Altered 'sheet_id' to be nullable in triggers table.")
        except Exception as e:
            print(f"- Error making sheet_id nullable: {e}")
            conn.rollback()
            cur = conn.cursor()
            
        conn.commit()
        cur.close()
        conn.close()
        print("\n✅ Database schema updated successfully!")
        
    except Exception as e:
        print(f"❌ Critical error: {e}")

if __name__ == "__main__":
    update_db_schema()
