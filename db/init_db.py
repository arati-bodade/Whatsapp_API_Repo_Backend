import logging
from .base import Base, engine
# Import ALL models to ensure they're registered with Base.metadata
from models import *


logger = logging.getLogger("DB_INIT")

def init_db():
    """Create database tables and perform automatic migrations."""
    logger.info("Starting database initialization...")
    
    # Set a statement timeout to prevent hanging indefinitely on locks
    # 30 seconds should be plenty for metadata/ALTER operations
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SET statement_timeout = '30s'"))
            conn.commit()
    except Exception as e:
        logger.debug(f"Failed to set statement timeout: {e}")

    try:
        from sqlalchemy.exc import IntegrityError
        logger.info("Synchronizing SQLAlchemy metadata (create_all)...")
        Base.metadata.create_all(bind=engine, checkfirst=True)
        logger.info("SQLAlchemy metadata synchronization complete")
    except IntegrityError as e:
        # Handle race condition where another process created the types/tables simultaneously
        logger.warning(f"Database initialization race condition detected (safe to ignore if other workers succeed): {e}")
    except Exception as e:
        logger.error(f"Error initializing database metadata: {e}")
    
    # 🔥 AUTOMATIC MIGRATION: Sync businesses table with Master Admin hierarchy
    try:
        with engine.connect() as conn:
            logger.info("Running automatic schema migrations...")
            
            # 1. Update businesses table columns
            # We use IF NOT EXISTS equivalents where possible or rely on try-except
            alter_commands = [
                "ALTER TABLE businesses ADD COLUMN IF NOT EXISTS parent_admin_id UUID",
                "ALTER TABLE businesses ADD COLUMN IF NOT EXISTS parent_role VARCHAR(50) DEFAULT 'reseller'",
                "ALTER TABLE businesses ADD COLUMN IF NOT EXISTS consumption_rate FLOAT DEFAULT 0.0",
                "ALTER TABLE businesses ADD COLUMN IF NOT EXISTS plan_name VARCHAR(255)",
                "ALTER TABLE businesses ADD COLUMN IF NOT EXISTS plan_id UUID",
                "ALTER TABLE businesses ADD COLUMN IF NOT EXISTS parent_reseller_id UUID", # Just in case
                "ALTER TABLE businesses ADD COLUMN IF NOT EXISTS plan_expiry TIMESTAMP WITH TIME ZONE",
                "ALTER TABLE businesses ALTER COLUMN parent_reseller_id DROP NOT NULL"
            ]
            
            for cmd in alter_commands:
                try:
                    conn.execute(text(cmd))
                    conn.commit()
                except Exception as e:
                    # Ignore if column already exists or other minor issues
                    conn.rollback()
                    
            logger.info("Checked/Synchronized businesses table schema")
            
            # 2. Increase status column length in message_logs
            try:
                logger.info("📏 Checking/Updating message_logs.status length...")
                conn.execute(text("ALTER TABLE message_logs ALTER COLUMN status TYPE VARCHAR(255)"))
                conn.commit()
                logger.info("Applied migration: Ensured message_logs.status length is 255")
            except Exception as e:
                # Ignore if table doesn't exist yet or column already correct or locked
                conn.rollback()
                logger.warning(f"Notice: Skipping message_logs status alter (already done or locked): {e}")
                
    except Exception as e:
        # Ignore if table doesn't exist yet or column already correct
        logger.error(f"Database migration block failed: {e}")
        pass

    logger.info("Database initialization finished")


