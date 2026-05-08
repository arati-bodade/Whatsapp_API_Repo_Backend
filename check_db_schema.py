from db.session import engine
from sqlalchemy import text
import sys

def check_schema():
    print("Checking message_usage_credit_logs schema...")
    with engine.connect() as conn:
        res = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'message_usage_credit_logs'"))
        rows = res.fetchall()
        if not rows:
            print("Table not found!")
            return
        for row in rows:
            print(f"{row[0]}: {row[1]}")

if __name__ == "__main__":
    check_schema()
