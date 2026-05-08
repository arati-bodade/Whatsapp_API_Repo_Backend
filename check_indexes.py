from db.session import SessionLocal
from sqlalchemy import text

def check_indexes():
    db = SessionLocal()
    try:
        # Check indexes for common tables
        for table in ['businesses', 'resellers', 'devices', 'credit_distributions']:
            query = text(f"SELECT indexname, indexdef FROM pg_indexes WHERE tablename = '{table}'")
            results = db.execute(query).fetchall()
            print(f"--- Table: {table} ---")
            for r in results:
                print(f"  {r[0]}: {r[1]}")
    finally:
        db.close()

if __name__ == "__main__":
    check_indexes()
