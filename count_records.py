import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def count_records():
    db_url = os.getenv("DATABASE_URL")
    if "?sslmode=require" not in db_url:
        db_url += "?sslmode=require"
    
    engine = create_engine(db_url)
    try:
        with engine.connect() as connection:
            tables = ['businesses', 'devices', 'google_sheet_triggers', 'master_admins', 'plans']
            for table in tables:
                result = connection.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                print(f"Table {table}: {count} records")
                
                if count > 0:
                    # Sample record comparison
                    if table == 'businesses':
                        res = connection.execute(text(f"SELECT busi_user_id, email, status FROM {table} LIMIT 1"))
                        row = res.fetchone()
                        print(f"  Sample {table}: ID={row[0]}, Email={row[1]}, Status={row[2]}")
                    elif table == 'devices':
                        res = connection.execute(text(f"SELECT device_id, busi_user_id, session_status FROM {table} LIMIT 1"))
                        row = res.fetchone()
                        print(f"  Sample {table}: ID={row[0]}, UserID={row[1]}, Status={row[2]}")

    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    count_records()
