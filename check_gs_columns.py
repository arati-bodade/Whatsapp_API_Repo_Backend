from sqlalchemy import create_engine, MetaData, Table, inspect
import os
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv("DATABASE_URL")
if not db_url:
    print("No DB URL")
    exit(1)

engine = create_engine(db_url)
inspector = inspect(engine)

columns = inspector.get_columns("google_sheet_triggers")
col_names = [col['name'] for col in columns]

print("Columns in google_sheet_triggers:")
for c in col_names:
    print(f"- {c}")

if "send_time_column" not in col_names:
    print("\n⚠️ 'send_time_column' IS MISSING!")
    
if "message_column" not in col_names:
    print("\n⚠️ 'message_column' IS MISSING!")
