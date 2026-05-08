import sys
import os
from sqlalchemy import create_engine, text

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from db.base import engine

def migrate_google_sheets_v3():
    print("Starting V3 migration for google_sheets table...")
    
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            # 1. Handle sheet_id vs id collision
            # If both exist, we assume 'id' is the one we want to keep (or was added by V2).
            # But we should make sure we don't lose data? 
            # Ideally we'd copy sheet_id to id if id is null, but assuming simple fix for now:
            # Drop sheet_id if it exists AND id exists.
            print("Checking schema for sheet_id/id collision...")
            
            # Check if sheet_id exists
            check_sheet_id = text("SELECT 1 FROM information_schema.columns WHERE table_name='google_sheets' AND column_name='sheet_id'")
            has_sheet_id = conn.execute(check_sheet_id).scalar()
            
            # Check if id exists
            check_id = text("SELECT 1 FROM information_schema.columns WHERE table_name='google_sheets' AND column_name='id'")
            has_id = conn.execute(check_id).scalar()
            
            if has_sheet_id and has_id:
                print("Both 'sheet_id' and 'id' exist. Dropping 'sheet_id'...")
                conn.execute(text("ALTER TABLE google_sheets DROP COLUMN sheet_id"))
            elif has_sheet_id and not has_id:
                print("'sheet_id' exists but 'id' does not. Renaming 'sheet_id' to 'id'...")
                conn.execute(text("ALTER TABLE google_sheets RENAME COLUMN sheet_id TO id"))
            else:
                print("No 'sheet_id' collision to resolve.")

            # 2. Handle rows_count vs total_rows
            print("Checking schema for rows_count/total_rows...")
            
            check_rows_count = text("SELECT 1 FROM information_schema.columns WHERE table_name='google_sheets' AND column_name='rows_count'")
            has_rows_count = conn.execute(check_rows_count).scalar()
            
            check_total_rows = text("SELECT 1 FROM information_schema.columns WHERE table_name='google_sheets' AND column_name='total_rows'")
            has_total_rows = conn.execute(check_total_rows).scalar()
            
            if has_rows_count and not has_total_rows:
                print("Renaming 'rows_count' to 'total_rows'...")
                conn.execute(text("ALTER TABLE google_sheets RENAME COLUMN rows_count TO total_rows"))
            elif has_rows_count and has_total_rows:
                print("Both 'rows_count' and 'total_rows' exist. Dropping 'rows_count' (assuming data migrated or irrelevant)...")
                conn.execute(text("ALTER TABLE google_sheets DROP COLUMN rows_count"))
            elif not has_total_rows:
                 print("Adding missing 'total_rows' column...")
                 conn.execute(text("ALTER TABLE google_sheets ADD COLUMN total_rows INTEGER DEFAULT 0"))

            # 3. Add other missing columns if they don't exist (Idempotent checks)
            print("Ensuring other columns exist...")
            missing_cols = [
                ("worksheet_name", "VARCHAR DEFAULT 'Sheet1'"),
                ("trigger_enabled", "BOOLEAN DEFAULT FALSE"),
                ("device_id", "VARCHAR NULL"),
                ("message_template", "TEXT NULL"),
                ("trigger_config", "JSON DEFAULT NULL"),
                ("created_at", "TIMESTAMP DEFAULT NOW()"),
                ("updated_at", "TIMESTAMP DEFAULT NOW()")
            ]
            
            for col_name, col_def in missing_cols:
                check_col = text(f"SELECT 1 FROM information_schema.columns WHERE table_name='google_sheets' AND column_name='{col_name}'")
                if not conn.execute(check_col).scalar():
                    print(f"Adding missing column '{col_name}'...")
                    conn.execute(text(f"ALTER TABLE google_sheets ADD COLUMN {col_name} {col_def}"))
            
            trans.commit()
            print("Migration V3 completed successfully.")
            
        except Exception as e:
            trans.rollback()
            print(f"Migration V3 Failed: {e}")
            raise e

if __name__ == "__main__":
    migrate_google_sheets_v3()
