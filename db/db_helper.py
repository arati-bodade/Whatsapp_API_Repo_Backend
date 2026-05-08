"""
Database helper functions for production-ready DB operations.
Provides semaphore-controlled DB access with exponential backoff retry.
"""
import logging
import asyncio
from functools import wraps
from typing import Callable, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from db.session import SessionLocal, db_semaphore

logger = logging.getLogger("DB_HELPER")


async def with_semaphore(coro):
    """
    Execute a coroutine with DB semaphore control.
    Limits concurrent DB operations to prevent pool overflow.
    """
    async with db_semaphore:
        return await coro


def async_db_operation(max_retries: int = 3, base_delay: float = 0.5):
    """
    Decorator for async DB operations with exponential backoff retry.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay for exponential backoff in seconds
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    # Execute with semaphore control
                    return await with_semaphore(func(*args, **kwargs))
                except OperationalError as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)  # Exponential backoff
                        logger.warning(
                            f"🔄 DB OperationalError (attempt {attempt + 1}/{max_retries}): {e}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"❌ DB OperationalError: Max retries ({max_retries}) reached")
                except SQLAlchemyError as e:
                    last_exception = e
                    logger.error(f"❌ DB SQLAlchemyError: {e}")
                    break  # Don't retry non-operational SQL errors
                except Exception as e:
                    last_exception = e
                    logger.error(f"❌ Unexpected error in DB operation: {e}")
                    break  # Don't retry unexpected errors
            
            raise last_exception if last_exception else Exception("DB operation failed")
        
        return wrapper
    return decorator


def get_db_session():
    """
    Context manager for DB sessions with proper cleanup.
    Use this for manual session management outside FastAPI dependencies.
    
    Usage:
        with get_db_session() as db:
            # DB operations
            pass
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
        db.close()
        logger.debug(f"🔒 DB session closed: {id(db)}")


async def execute_db_operation(operation_func: Callable, *args, **kwargs) -> Any:
    """
    Execute a DB operation with semaphore control and proper session management.
    
    Args:
        operation_func: Function that takes a db session as first argument
        *args: Additional arguments for operation_func
        **kwargs: Additional keyword arguments for operation_func
    
    Returns:
        Result of the operation
    
    Example:
        async def get_user(db, user_id):
            return db.query(User).filter(User.id == user_id).first()
        
        user = await execute_db_operation(get_user, user_id="123")
    """
    async with db_semaphore:
        with get_db_session() as db:
            try:
                # If operation is a coroutine, await it
                if asyncio.iscoroutinefunction(operation_func):
                    return await operation_func(db, *args, **kwargs)
                else:
                    return operation_func(db, *args, **kwargs)
            except Exception as e:
                logger.error(f"❌ DB operation failed: {e}")
                if db.in_transaction():
                    db.rollback()
                raise e
