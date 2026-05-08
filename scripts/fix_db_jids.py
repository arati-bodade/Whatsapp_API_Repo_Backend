
import sys
import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.session import SessionLocal, engine
from models.whatsapp_inbox import WhatsAppInbox

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DB_CLEANUP")

def fix_corrupted_jids():
    session = SessionLocal()

    try:
        logger.info("🚀 Starting DB JID Cleanup...")
        
        # 1. Check for remote_jid column
        with engine.connect() as conn:
            result_cols = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'whatsapp_inbox'"))
            columns = [r[0] for r in result_cols.fetchall()]
            logger.info(f"DB Columns: {columns}")
            
            has_remote_jid = 'remote_jid' in columns
            
            if has_remote_jid:
                logger.info("✅ Found 'remote_jid' column. Executing User's SQL Fix...")
                # Run the exact SQL user asked for
                # postgres split_part, sqlite substr... assuming postgres from psycopg2 errors seen before.
                sql = text("""
                    UPDATE whatsapp_inbox
                    SET phone_number = split_part(remote_jid, '@', 1)
                    WHERE phone_number IS NULL
                       OR LENGTH(phone_number) > 14;
                """)
                result = conn.execute(sql)
                conn.commit()
                logger.info(f"✅ SQL Fix Executed. Rows affected: {result.rowcount}")
            else:
                logger.warning("❌ 'remote_jid' column NOT found. Falling back to heuristic cleanup.")
                # Fallback: Delete rows with invalid phones (Len > 14)
                # We use > 14 because 15-digit IDs were reported. 
                # Valid phones are typically <= 13 (e.g. 91 + 10 digits).
                # Exception: Some IoT M2M might be 15? But user says 15 digit is bad ID.
                
                # Check count first
                check_sql = text("SELECT COUNT(*) FROM whatsapp_inbox WHERE LENGTH(phone_number) > 14")
                count = conn.execute(check_sql).scalar()
                
                if count > 0:
                    logger.info(f"Deleting {count} rows with suspicious phone length (>14)...")
                    del_sql = text("DELETE FROM whatsapp_inbox WHERE LENGTH(phone_number) > 14")
                    conn.execute(del_sql)
                    conn.commit()
                    logger.info("✅ Cleanup Complete.")
                else:
                    logger.info("✅ No suspicious rows found (Length > 14).")

    except Exception as e:
        logger.error(f"Cleanup failed: {e}")

if __name__ == "__main__":
    fix_corrupted_jids()
