from db.base import engine
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("schema_update")

def update_schema():
    with engine.connect() as conn:
        # Check sheet_trigger_history
        res = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'sheet_trigger_history'"))
        cols = [r[0] for r in res]
        logger.info(f"Columns in sheet_trigger_history: {cols}")
        
        if 'device_id' not in cols:
            logger.info("Adding device_id to sheet_trigger_history...")
            conn.execute(text("ALTER TABLE sheet_trigger_history ADD COLUMN device_id UUID"))
        
        if 'trigger_id' not in cols:
            logger.info("Adding trigger_id to sheet_trigger_history...")
            conn.execute(text("ALTER TABLE sheet_trigger_history ADD COLUMN trigger_id VARCHAR"))
        
        # Check google_sheet_triggers
        res = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'google_sheet_triggers'"))
        cols = [r[0] for r in res]
        logger.info(f"Columns in google_sheet_triggers: {cols}")
        
        if 'message_column' not in cols:
            logger.info("Adding message_column to google_sheet_triggers...")
            conn.execute(text("ALTER TABLE google_sheet_triggers ADD COLUMN message_column TEXT"))
        
        if 'status_column' not in cols:
            logger.info("Adding status_column to google_sheet_triggers...")
            conn.execute(text("ALTER TABLE google_sheet_triggers ADD COLUMN status_column VARCHAR"))
        
        if 'trigger_value' not in cols:
            logger.info("Adding trigger_value to google_sheet_triggers...")
            conn.execute(text("ALTER TABLE google_sheet_triggers ADD COLUMN trigger_value VARCHAR"))
        
        # Check google_sheets
        res = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'google_sheets'"))
        cols = [r[0] for r in res]
        logger.info(f"Columns in google_sheets: {cols}")
        
        if 'device_id' not in cols:
            logger.info("Adding device_id to google_sheets...")
            conn.execute(text("ALTER TABLE google_sheets ADD COLUMN device_id UUID"))

        conn.commit()
        logger.info("Schema updates complete")

if __name__ == "__main__":
    update_schema()
