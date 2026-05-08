import logging
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.config import settings

logger = logging.getLogger("DB_SESSION")

# 🔥 CONCURRENCY CONTROL: Semaphore to limit parallel DB calls
db_semaphore = asyncio.Semaphore(10)  # Max 10 concurrent DB operations

# 1. Create Engine with pool_pre_ping for stability
engine = settings.engine

# 2. SessionLocal - No global scoped_session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. get_db Dependency generator
def get_db():
    """
    FastAPI dependency that provides a fresh session per request with proper cleanup.
    CRITICAL: Always closes session in finally block to prevent connection leaks.
    """
    db = SessionLocal()
    try:
        logger.debug(f"🔓 DB session opened: {id(db)}")
        yield db
    except Exception as e:
        logger.error(f"❌ DB session error: {e}")
        if db.in_transaction():
            db.rollback()
        raise e
    finally:
        # CRITICAL: Always close session to prevent connection leaks
        db.close()
        logger.debug(f"🔒 DB session closed: {id(db)}")
