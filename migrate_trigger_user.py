import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def update_db_schema():
    print(f"Connecting to database to add user_id column to triggers...")
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # 1. Add user_id to google_sheet_triggers
        try:
            cur.execute("ALTER TABLE google_sheet_triggers ADD COLUMN user_id UUID;")
            print("- Added 'user_id' to 'google_sheet_triggers' table.")
        except Exception as e:
            if "already exists" in str(e):
                print("- 'user_id' already exists.")
            else:
                print(f"- Error adding user_id: {e}")
            conn.rollback()
            cur = conn.cursor()
            
        # 2. Backfill user_id from linked sheets
        try:
            cur.execute("""
                UPDATE google_sheet_triggers t
                SET user_id = s.user_id
                FROM google_sheets s
                WHERE t.sheet_id = s.id AND t.user_id IS NULL;
            """)
            print("- Backfilled user_id from linked Google Sheets.")
        except Exception as e:
            print(f"- Error backfilling user_id: {e}")
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
