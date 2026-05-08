from sqlalchemy import text
from db.session import SessionLocal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_all():
    db = SessionLocal()
    try:
        # Table, Column
        targets = [
            ("businesses", "busi_user_id"),
            ("businesses", "parent_reseller_id"),
            ("businesses", "parent_admin_id"),
            ("businesses", "plan_id"),
            ("businesses", "created_by"),
            
            ("devices", "device_id"),
            ("devices", "busi_user_id"),
            
            ("google_sheets", "id"),
            ("google_sheets", "user_id"),
            ("google_sheets", "device_id"),
            
            ("google_sheet_triggers", "trigger_id"),
            ("google_sheet_triggers", "user_id"),
            ("google_sheet_triggers", "sheet_id"),
            ("google_sheet_triggers", "device_id"),
            
            ("sheet_trigger_history", "id"),
            ("sheet_trigger_history", "sheet_id"),
            ("sheet_trigger_history", "trigger_id"),
            ("sheet_trigger_history", "device_id"),
            
            ("whatsapp_messages", "device_id"),
            ("whatsapp_messages", "busi_user_id"),
        ]
        
        for table, col in targets:
            logger.info(f"Converting {table}.{col} to UUID...")
            try:
                # 1. First, check current type
                res = db.execute(text(f"SELECT data_type FROM information_schema.columns WHERE table_name = '{table}' AND column_name = '{col}'"))
                current_type = res.scalar()
                
                if current_type == 'uuid':
                    logger.info(f"   - {table}.{col} is already UUID. Skipping.")
                    continue
                
                # 2. Perform conversion
                # We use USING col::uuid to handle the conversion from string
                db.execute(text(f"ALTER TABLE {table} ALTER COLUMN {col} TYPE UUID USING {col}::uuid"))
                db.commit()
                logger.info(f"   ✅ Successfully converted {table}.{col}")
            except Exception as e:
                db.rollback()
                logger.error(f"   ❌ Failed to convert {table}.{col}: {e}")
                
    finally:
        db.close()

if __name__ == "__main__":
    migrate_all()
