import logging
from sqlalchemy import text
from db.base import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SCHEMA_UPDATE")

def update_schema():
    logger.info("🚀 Starting Schema Update for 'messages' table...")
    
    commands = [
        "ALTER TABLE messages ADD COLUMN IF NOT EXISTS engine_message_id VARCHAR(100);",
        "ALTER TABLE messages ADD COLUMN IF NOT EXISTS delivered_at TIMESTAMP WITH TIME ZONE;",
        "ALTER TABLE messages ADD COLUMN IF NOT EXISTS read_at TIMESTAMP WITH TIME ZONE;",
        "CREATE INDEX IF NOT EXISTS ix_messages_engine_message_id ON messages (engine_message_id);"
    ]
    
    with engine.connect() as conn:
        for sql in commands:
            try:
                logger.info(f"Executing: {sql}")
                conn.execute(text(sql))
                conn.commit()
                logger.info("✅ Success")
            except Exception as e:
                logger.error(f"❌ Failed: {e}")
                
    logger.info("✨ Schema Update Completed!")

if __name__ == "__main__":
    update_schema()
