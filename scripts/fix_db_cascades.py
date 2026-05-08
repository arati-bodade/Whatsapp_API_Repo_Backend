import sys
import os
from sqlalchemy import text

def fix_cascades():
    from db.session import SessionLocal
    db = SessionLocal()
    try:
        print("🔍 Starting database cascade fix...")
        
        # List of constraints to drop and recreate with CASCADE
        # format: (table, constraint_name, column, referenced_table, referenced_column)
        constraints = [
            ("campaigns", "campaigns_sheet_id_fkey", "sheet_id", "google_sheets", "id"),
            ("campaigns", "campaigns_busi_user_id_fkey", "busi_user_id", "businesses", "busi_user_id"),
            ("google_sheets", "google_sheets_user_id_fkey", "user_id", "businesses", "busi_user_id"),
            ("google_sheet_triggers", "google_sheet_triggers_sheet_id_fkey", "sheet_id", "google_sheets", "id"),
            ("sheet_trigger_history", "sheet_trigger_history_sheet_id_fkey", "sheet_id", "google_sheets", "id"),
            ("campaign_devices", "campaign_devices_campaign_id_fkey", "campaign_id", "campaigns", "id"),
            ("message_templates", "message_templates_campaign_id_fkey", "campaign_id", "campaigns", "id"),
            ("message_logs", "message_logs_campaign_id_fkey", "campaign_id", "campaigns", "id")
        ]
        
        for table, name, col, ref_table, ref_col in constraints:
            print(f"🔄 Processing {table}.{name}...")
            
            # Check if constraint exists before dropping
            check_sql = text(f"""
                SELECT COUNT(*) FROM information_schema.table_constraints 
                WHERE constraint_name = '{name}' AND table_name = '{table}'
            """)
            exists = db.execute(check_sql).scalar() > 0
            
            if exists:
                print(f"  - Dropping existing constraint {name}")
                db.execute(text(f"ALTER TABLE {table} DROP CONSTRAINT {name}"))
            
            print(f"  - Creating new constraint {name} with ON DELETE CASCADE")
            db.execute(text(f"""
                ALTER TABLE {table} 
                ADD CONSTRAINT {name} 
                FOREIGN KEY ({col}) 
                REFERENCES {ref_table} ({ref_col}) 
                ON DELETE CASCADE
            """))
            
        db.commit()
        print("✅ Database cascade fix completed successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error fixing cascades: {e}")
        # Try to find the actual constraint names if they differ
        try:
            print("🕵️ Attempting to discover actual constraint names...")
            discovery_sql = text("""
                SELECT 
                    tc.table_name, 
                    kcu.column_name, 
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name,
                    tc.constraint_name
                FROM 
                    information_schema.table_constraints AS tc 
                    JOIN information_schema.key_column_usage AS kcu
                      ON tc.constraint_name = kcu.constraint_name
                      AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage AS ccu
                      ON ccu.constraint_name = tc.constraint_name
                      AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_name IN ('campaigns', 'google_sheets');
            """)
            results = db.execute(discovery_sql).fetchall()
            for row in results:
                print(f"  Found: {row.table_name}.{row.column_name} -> {row.foreign_table_name} ({row.constraint_name})")
        except:
            pass
    finally:
        db.close()

if __name__ == "__main__":
    # Add project root to sys.path to allow imports (e.g., from 'db', 'models')
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    sys.path.append(project_root)
    fix_cascades()
