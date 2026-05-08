import logging
import asyncio
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from .base import engine

logger = logging.getLogger("DB_SESSION")

# 🔥 CONCURRENCY CONTROL: Semaphore to limit parallel DB calls
db_semaphore = asyncio.Semaphore(10)  # Max 10 concurrent DB operations

# 1. Plain sessionmaker - NO scoped_session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=engine)

def get_db():
    """
    FastAPI dependency that provides a fresh session per request with proper cleanup.
    CRITICAL: Always closes session in finally block to prevent connection leaks.
    """
    db = SessionLocal()
    try:
        logger.debug(f"🔓 DB session opened: {id(db)}")
        yield db
    except OperationalError as e:
        logger.error(f"❌ DB OperationalError: {e}")
        if db.in_transaction():
            db.rollback()
        raise e
    except Exception as e:
        logger.error(f"❌ DB session error: {e}")
        if db.in_transaction():
            db.rollback()
        raise e
    finally:
        # CRITICAL: Always close session to prevent connection leaks
        db.close()
        logger.debug(f"🔒 DB session closed: {id(db)}")
