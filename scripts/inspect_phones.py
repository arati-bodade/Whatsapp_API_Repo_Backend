
import sys
import os
import logging
from sqlalchemy import create_engine, text, inspect

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.session import SessionLocal, engine

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DB_INSPECT")

def inspect_db():
    session = SessionLocal()
    try:
        # 2. Dump distinct phone numbers
        logger.info("--- DUMPING DISTINCT PHONE NUMBERS ---")
        
        # Use simpler raw interaction
        with engine.connect() as conn:
            # 1. Get Columns
            try:
                result_cols = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'whatsapp_inbox'"))
                columns = [r[0] for r in result_cols.fetchall()]
                logger.info(f"Actual DB Columns: {columns}")
            except Exception as e:
                logger.error(f"Failed to get columns: {e}")

            # 2. Get Phones (Commented out for now to ensure we see columns)
            # logger.info("--- DUMPING PHONES ---")
            result = conn.execute(text("SELECT phone_number FROM whatsapp_inbox LIMIT 20"))
            phones = [r[0] for r in result]
            
            for p in phones:
                 logger.info(f"Phone: {p} (Len: {len(str(p))})")
            
    except Exception as e:
        logger.error(f"Inspection failed: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    inspect_db()
