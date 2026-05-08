import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def update_db_schema():
    print(f"Connecting to database to add scheduled_at columns...")
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # 1. Add scheduled_at to campaigns
        try:
            cur.execute("ALTER TABLE campaigns ADD COLUMN scheduled_at TIMESTAMP WITH TIME ZONE;")
            print("- Added 'scheduled_at' to 'campaigns' table.")
        except Exception as e:
            if "already exists" in str(e):
                print("- 'scheduled_at' already exists in 'campaigns' table.")
            else:
                print(f"- Error updating 'campaigns' table: {e}")
            conn.rollback()
            cur = conn.cursor()
            
        # 2. Add scheduled_at to google_sheet_triggers
        try:
            cur.execute("ALTER TABLE google_sheet_triggers ADD COLUMN scheduled_at TIMESTAMP WITH TIME ZONE;")
            print("- Added 'scheduled_at' to 'google_sheet_triggers' table.")
        except Exception as e:
            if "already exists" in str(e):
                print("- 'scheduled_at' already exists in 'google_sheet_triggers' table.")
            else:
                print(f"- Error updating 'google_sheet_triggers' table: {e}")
            conn.rollback()
            cur = conn.cursor()
            
        conn.commit()
        cur.close()
        conn.close()
        print("\n✅ Database schema updated successfully!")
        
    except Exception as e:
        print(f"❌ Critical error connecting to database: {e}")

if __name__ == "__main__":
    update_db_schema()
