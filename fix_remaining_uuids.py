from sqlalchemy import text
from db.session import SessionLocal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate():
    db = SessionLocal()
    try:
        # Tables and columns to convert to UUID
        migrations = [
            ("businesses", "created_by"),
            ("google_sheet_triggers", "device_id"),
            ("google_sheets", "device_id"),
        ]
        
        for table, col in migrations:
            logger.info(f"Converting {table}.{col} to UUID...")
            try:
                # 1. Drop constraints if needed (optional for these columns)
                # 2. Convert using USING column::uuid
                db.execute(text(f"ALTER TABLE {table} ALTER COLUMN {col} TYPE UUID USING {col}::uuid"))
                db.commit()
                logger.info(f"✅ Successfully converted {table}.{col}")
            except Exception as e:
                db.rollback()
                logger.error(f"❌ Failed to convert {table}.{col}: {e}")
                
    finally:
        db.close()

if __name__ == "__main__":
    migrate()
