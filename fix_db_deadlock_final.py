from sqlalchemy import text
from core.config import settings
from sqlalchemy.orm import sessionmaker
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DB_CLEANUP")

def cleanup_sessions():
    engine = settings.engine
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        logger.info("🧹 Starting database session cleanup...")
        
        # 1. Kill idle-in-transaction sessions
        # Note: We can only kill sessions that aren't our own
        kill_query = text("""
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE state = 'idle in transaction'
            AND pid <> pg_backend_pid();
        """)
        result = session.execute(kill_query)
        logger.info(f"✅ Terminated idle-in-transaction sessions.")
        
        session.commit()
    except Exception as e:
        logger.error(f"❌ Cleanup failed: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    cleanup_sessions()
