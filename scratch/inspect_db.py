import os
import uuid
from sqlalchemy import create_url, create_engine, text
from datetime import datetime

DATABASE_URL = "postgresql://whatsapp_platform_fn0k_user:AbHezwfAs553dVCy33wfHzsGMVJbf8M0@dpg-d6oh8tfafjfc7386oii0-a.oregon-postgres.render.com/whatsapp_platform_fn0k?sslmode=require"

engine = create_engine(DATABASE_URL)

def inspect():
    with engine.connect() as conn:
        print("--- TRIGGERS ---")
        triggers = conn.execute(text("SELECT trigger_id, is_enabled, scheduled_at, last_triggered_at FROM google_sheet_triggers")).fetchall()
        for t in triggers:
            print(f"ID: {t[0]}, Enabled: {t[1]}, Scheduled: {t[2]}, Last: {t[3]}")
            
        print("\n--- HISTORY (Last 5) ---")
        history = conn.execute(text("SELECT triggered_at, status, phone_number, error_message FROM google_sheet_trigger_history ORDER BY triggered_at DESC LIMIT 5")).fetchall()
        for h in history:
            print(f"Time: {h[0]}, Status: {h[1]}, Phone: {h[2]}, Error: {h[3]}")

if __name__ == "__main__":
    inspect()
