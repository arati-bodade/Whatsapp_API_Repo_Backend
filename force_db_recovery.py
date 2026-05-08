from db.session import SessionLocal
from sqlalchemy import text

def kill_everything():
    db = SessionLocal()
    try:
        # 1. Kill everything except our own PID
        query = text("""
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE pid <> pg_backend_pid()
              AND datname = current_database()
        """)
        results = db.execute(query).fetchall()
        print(f"Force terminated {len(results)} sessions.")
        db.commit()
    except Exception as e:
        print(f"Error killing sessions: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    kill_everything()
