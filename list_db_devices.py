
import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("DATABASE_URL not found in .env")
    sys.exit(1)

engine = create_engine(DATABASE_URL)

def list_devices():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT device_id, device_name, session_status, last_active FROM devices"))
        rows = result.fetchall()
        print(f"Total devices in DB: {len(rows)}")
        for row in rows:
            print(f"ID: {row[0]}, Name: {row[1]}, Status: {row[2]}, Last Active: {row[3]}")

if __name__ == "__main__":
    list_devices()
