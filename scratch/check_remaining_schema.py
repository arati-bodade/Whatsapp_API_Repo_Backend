
from db.session import get_db
from sqlalchemy import text

db = next(get_db())
try:
    for table in ['google_sheet_triggers', 'message_usage_credit_logs', 'audit_logs']:
        print(f"\n--- {table} ---")
        result = db.execute(text(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}'"))
        for row in result:
            print(f"{row[0]}: {row[1]}")
finally:
    db.close()
