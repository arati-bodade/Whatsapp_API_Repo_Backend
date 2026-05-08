"""
Fix Multi Web Device Unique Constraint Issue

Revision ID: replace_device_unique_constraint
Revises: 019_remove_device_id_from_google_sheets
Create Date: 2026-02-27 17:30:00.000000

"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from db.base import engine

def upgrade():
    print("🔄 Starting device constraint migration...")
    
    try:
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            # 1. Drop the old indexes
            print("➖ Dropping old unique index uniq_user_web_device...")
            try:
                conn.execute(text("""
                    DROP INDEX IF EXISTS uniq_user_web_device
                """))
                print("✅ Old index uniq_user_web_device dropped successfully")
            except Exception as e:
                print(f"⚠️ Old index might not exist: {e}")
                
            try:
                conn.execute(text("""
                    DROP INDEX IF EXISTS uq_web_device
                """))
                print("✅ Old index uq_web_device dropped successfully")
            except Exception as e:
                print(f"⚠️ Old index uq_web_device might not exist: {e}")
                
            # 1.5 Deduplicate existing device names
            print("🔍 Ensuring no duplicate device names exist before adding constraint...")
            try:
                # Append the first 4 chars of device_id to the device name if there are duplicates
                conn.execute(text("""
                    WITH duplicates AS (
                      SELECT device_id, busi_user_id, device_name,
                             ROW_NUMBER() OVER(PARTITION BY busi_user_id, device_name ORDER BY created_at) as rn
                      FROM devices
                    )
                    UPDATE devices
                    SET device_name = devices.device_name || ' (' || SUBSTRING(devices.device_id::text, 1, 4) || ')'
                    FROM duplicates
                    WHERE devices.device_id = duplicates.device_id AND duplicates.rn > 1;
                """))
                print("✅ Duplicates cleaned up successfully")
            except Exception as e:
                print(f"⚠️ Failed to deduplicate: {e}")

            # 2. Add the new constraint
            print("➕ Adding new constraint uniq_user_device_name...")
            try:
                conn.execute(text("""
                    ALTER TABLE devices 
                    ADD CONSTRAINT uniq_user_device_name UNIQUE (busi_user_id, device_name)
                """))
                print("✅ New constraint added successfully")
            except Exception as e:
                print(f"⚠️ Failed to add new constraint: {e}")
                
            print("✅ Migration completed successfully!")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise

def downgrade():
    print("🔄 Reverting device constraint migration...")
    
    try:
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            # 1. Drop the new constraint
            print("➖ Dropping constraint uniq_user_device_name...")
            try:
                conn.execute(text("""
                    ALTER TABLE devices 
                    DROP CONSTRAINT IF EXISTS uniq_user_device_name
                """))
                
                conn.execute(text("""
                    DROP INDEX IF EXISTS uniq_user_device_name
                """))
                print("✅ New constraint/index dropped successfully")
            except Exception as e:
                print(f"⚠️ New constraint might not exist: {e}")
                
            # 2. Re-create the old indexes
            print("➕ Adding old unique index uniq_user_web_device...")
            try:
                conn.execute(text("""
                    CREATE UNIQUE INDEX uniq_user_web_device 
                    ON devices (busi_user_id, device_type) 
                    WHERE device_type = 'web' AND deleted_at IS NULL
                """))
                print("✅ Old index re-added successfully")
            except Exception as e:
                print(f"⚠️ Failed to re-add old index: {e}")
                
            print("✅ Downgrade completed successfully!")
            
    except Exception as e:
        print(f"❌ Downgrade failed: {e}")
        raise

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        downgrade()
    else:
        upgrade()
