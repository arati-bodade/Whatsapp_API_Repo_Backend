from db.session import SessionLocal
from sqlalchemy import text

def inspect_businesses():
    db = SessionLocal()
    try:
        rows = db.execute(text("SELECT * FROM businesses LIMIT 20")).fetchall()
        print(f"Found {len(rows)} rows in businesses (LIMIT 20):")
        for row in rows:
            print(row)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_businesses()
