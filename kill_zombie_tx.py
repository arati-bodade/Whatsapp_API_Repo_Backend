from db.session import SessionLocal
from sqlalchemy import text

def kill_idle_transactions():
    db = SessionLocal()
    try:
        # Kill transactions that have been 'idle in transaction' for more than 5 minutes
        # We use pid to terminate backend
        query = text("""
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE state = 'idle in transaction'
              AND (now() - state_change) > interval '5 minutes'
              AND pid <> pg_backend_pid()
        """)
        results = db.execute(query).fetchall()
        print(f"Terminated {len(results)} zombie transactions.")
        
        # Also kill if blocked for too long
        query2 = text("""
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE state = 'active'
              AND (now() - query_start) > interval '10 minutes'
              AND wait_event_type = 'Lock'
        """)
        results2 = db.execute(query2).fetchall()
        print(f"Terminated {len(results2)} blocked lock transactions.")
        
        db.commit()
    except Exception as e:
        print(f"Error killing transactions: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    kill_idle_transactions()
