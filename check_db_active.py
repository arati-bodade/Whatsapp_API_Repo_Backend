from db.session import SessionLocal
from sqlalchemy import text

def check_active_queries():
    db = SessionLocal()
    try:
        query = text("""
            SELECT query, state, wait_event_type, wait_event 
            FROM pg_stat_activity 
            WHERE state != 'idle' 
              AND query NOT LIKE '%pg_stat_activity%'
        """)
        results = db.execute(query).fetchall()
        print(f"Active queries found: {len(results)}")
        for i, row in enumerate(results):
            print(f"[{i}] Query: {row[0][:150]}")
            print(f"    State: {row[1]} | Wait: {row[2]}/{row[3]}")
    except Exception as e:
        print(f"Error checking status: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_active_queries()
