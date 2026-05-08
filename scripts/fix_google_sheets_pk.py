import sys
import os
import uuid
# Add parent directory to path to allow importing from main app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text, inspect
from db.base import Base
from models.google_sheet import GoogleSheet
from core.config import settings

def fix_google_sheets_schema():
    print("Connecting to database...")
    database_url = settings.DATABASE_URL
    engine = create_engine(database_url)
    connection = engine.connect()
    
    try:
        inspector = inspect(engine)
        columns = [c['name'] for c in inspector.get_columns('google_sheets')]
        pk = inspector.get_pk_constraint('google_sheets')
        
        info = f"Current columns: {columns}\nCurrent PK: {pk}\n"
        print(info)
        with open("fix_log.txt", "w") as f:
            f.write(info)

        # 0. Check and add 'worksheet_name' if missing
        if 'worksheet_name' not in columns:
            print("Adding 'worksheet_name' column...")
            connection.execute(text("ALTER TABLE google_sheets ADD COLUMN worksheet_name VARCHAR DEFAULT 'Sheet1'"))
            connection.commit() # Explicit commit
            # Refresh columns list
            columns.append('worksheet_name')

        # 1. Check if 'id' exists
        if 'id' not in columns:
            print("CRITICAL: 'id' column missing. Adding it...")
            connection.execute(text("ALTER TABLE google_sheets ADD COLUMN id VARCHAR"))
            connection.commit()
            
            # Using raw SQL to backfill
            rows = connection.execute(text("SELECT spreadsheet_id, worksheet_name FROM google_sheets")).fetchall()
            print(f"Backfilling UUIDs for {len(rows)} rows...")
            
            for row in rows:
                new_id = str(uuid.uuid4())
                sid = row[0]
                wname = row[1]
                connection.execute(text("UPDATE google_sheets SET id = :id WHERE spreadsheet_id = :sid AND worksheet_name = :wname"), 
                                   {"id": new_id, "sid": sid, "wname": wname})
            connection.commit()
            
            connection.execute(text("ALTER TABLE google_sheets ALTER COLUMN id SET NOT NULL"))
            connection.commit()
            
        else:
            print("'id' column exists.")

        # 2. Check Primary Key
        if 'id' not in pk['constrained_columns']:
            print("Fixing Primary Key to use 'id'...")
            # Drop existing PK if any
            if pk['name']:
                # Ensure we handle multiple columns if composite PK
                connection.execute(text(f"ALTER TABLE google_sheets DROP CONSTRAINT {pk['name']} CASCADE"))
                connection.commit()
            
            connection.execute(text("ALTER TABLE google_sheets ADD PRIMARY KEY (id)"))
            connection.commit()
            print("Primary Key set to 'id'.")
            
        # 3. Fix Foreign Key in sheet_trigger_history
        if inspector.has_table("sheet_trigger_history"):
            print("Checking sheet_trigger_history foreign key...")
            fks = inspector.get_foreign_keys("sheet_trigger_history")
            has_fk = False
            for fk in fks:
                if fk['referred_table'] == 'google_sheets' and fk['referred_columns'] == ['id']:
                    has_fk = True
                    break
            
            if not has_fk:
                 print("Adding FK constraint to sheet_trigger_history...")
                 try:
                     connection.execute(text("""
                        ALTER TABLE sheet_trigger_history 
                        ADD CONSTRAINT fk_sheet_trigger_history_google_sheets 
                        FOREIGN KEY (sheet_id) REFERENCES google_sheets(id) ON DELETE CASCADE
                     """))
                     connection.commit()
                     print("FK constraint added.")
                 except Exception as fk_err:
                     print(f"Warning: Could not add FK (maybe duplicates or missing column): {fk_err}")
        
        print("Schema fix completed successfully.")
        with open("fix_log.txt", "a") as f:
            f.write("\nSUCCESS: Schema fix completed.")

    except Exception as e:
        print(f"Error during schema fix: {e}")
        with open("fix_log.txt", "a") as f:
            f.write(f"\nERROR: {str(e)}")
    finally:
        connection.close()

if __name__ == "__main__":
    fix_google_sheets_schema()
