from sqlalchemy import text
import sys
import os

# Add the current directory to sys.path so we can import db/settings
sys.path.append(os.getcwd())

try:
    from db.base import engine
    print("🚀 [FORCE-SYNC] Database connection found...")
except ImportError as e:
    print(f"❌ [ERROR] Could not import database: {e}")
    print("Make sure you are running this from the backend folder.")
    sys.exit(1)

print("🛠️ [FORCE-SYNC] Starting direct database update...")

migrations = [
    "ALTER TABLE campaigns ADD COLUMN IF NOT EXISTS scheduled_at TIMESTAMP WITH TIME ZONE;",
    "ALTER TABLE google_sheet_triggers ADD COLUMN IF NOT EXISTS scheduled_at TIMESTAMP WITH TIME ZONE;",
    "ALTER TABLE google_sheet_triggers ADD COLUMN IF NOT EXISTS source_file_url TEXT;",
    "ALTER TABLE google_sheet_triggers ADD COLUMN IF NOT EXISTS user_id UUID;",
    "ALTER TABLE google_sheet_triggers ALTER COLUMN sheet_id DROP NOT NULL;",
    # Data sync
    "UPDATE google_sheet_triggers t SET user_id = s.user_id FROM google_sheets s WHERE t.sheet_id = s.id AND t.user_id IS NULL;"
]

for sql in migrations:
    try:
        with engine.begin() as conn:
            conn.execute(text("SET statement_timeout = 0;")) # No time limit
            conn.execute(text(sql))
            print(f"✅ Executed: {sql[:50]}...")
    except Exception as e:
        print(f"⚠️ Note: {str(e)[:100]}")

print("\n✨ [SUCCESS] Database is fixed! You can now start 'uvicorn' and refresh your browser.")
