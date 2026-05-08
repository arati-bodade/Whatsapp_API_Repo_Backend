from db.session import SessionLocal
from sqlalchemy import text

def query_indexes():
    db = SessionLocal()
    try:
        print("Querying indexes for 'businesses' table...")
        res = db.execute(text("SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'businesses'")).fetchall()
        if not res:
            print("No indexes found!")
        for r in res:
            print(f"Index: {r[0]} | Def: {r[1]}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    query_indexes()
