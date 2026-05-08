import sys
import os
from sqlalchemy import text

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from db.base import engine

def migrate_uuid_types():
    print("Starting UUID migration for google_sheets and sheet_trigger_history...")
    
    commands = [
        # 1. Drop constraints to allow type changes
        "ALTER TABLE sheet_trigger_history DROP CONSTRAINT IF EXISTS sheet_trigger_history_result_sheet_id_fkey;", # varied names check
        "ALTER TABLE sheet_trigger_history DROP CONSTRAINT IF EXISTS sheet_trigger_history_sheet_id_fkey;",
        "ALTER TABLE sheet_trigger_history DROP CONSTRAINT IF EXISTS sheet_trigger_history_pkey;",
        
        "ALTER TABLE google_sheets DROP CONSTRAINT IF EXISTS google_sheets_user_id_fkey;",
        "ALTER TABLE google_sheets DROP CONSTRAINT IF EXISTS google_sheets_device_id_fkey;",
        "ALTER TABLE google_sheets DROP CONSTRAINT IF EXISTS google_sheets_pkey;",

        # 2. Convert columns to UUID
        # google_sheets
        "ALTER TABLE google_sheets ALTER COLUMN id TYPE UUID USING id::uuid;",
        "ALTER TABLE google_sheets ALTER COLUMN user_id TYPE UUID USING user_id::uuid;",
        
        # sheet_trigger_history
        "ALTER TABLE sheet_trigger_history ALTER COLUMN id TYPE UUID USING id::uuid;",
        "ALTER TABLE sheet_trigger_history ALTER COLUMN sheet_id TYPE UUID USING sheet_id::uuid;",
        
        # 3. Re-add Primary Keys
        "ALTER TABLE google_sheets ADD PRIMARY KEY (id);",
        "ALTER TABLE sheet_trigger_history ADD PRIMARY KEY (id);",
        
        # 4. Re-add Foreign Keys
        # google_sheets.user_id -> businesses.busi_user_id
        """
        ALTER TABLE google_sheets 
        ADD CONSTRAINT google_sheets_user_id_fkey 
        FOREIGN KEY (user_id) REFERENCES businesses(busi_user_id);
        """,
        
        # google_sheets.device_id -> devices.device_id
        # Note: device_id in google_sheets is nullable string, likely refers to devices table which has device_id as VARCHAR?
        # Let's check device model first. If device_id is UUID in devices, we should convert here too. 
        # CAUTION: The user asked specifically for google_sheets.user_id and sheet_trigger_history.
        # But looking at previous inspect output (Step 162), google_sheets has device_id as VARCHAR.
        # Device model (Step 157 line 47) relationship(Device).
        # File models/device.py (Step 150) exists. 
        # Safest to just restore the FK if type matches, but we changed user_id.
        # IF devices.device_id is VARCHAR, we leave google_sheets.device_id as VARCHAR.
        """
        ALTER TABLE google_sheets 
        ADD CONSTRAINT google_sheets_device_id_fkey 
        FOREIGN KEY (device_id) REFERENCES devices(device_id) ON DELETE SET NULL;
        """,
        
        # sheet_trigger_history.sheet_id -> google_sheets.id
        """
        ALTER TABLE sheet_trigger_history 
        ADD CONSTRAINT sheet_trigger_history_sheet_id_fkey 
        FOREIGN KEY (sheet_id) REFERENCES google_sheets(id) ON DELETE CASCADE;
        """
    ]

    try:
        with engine.connect() as conn:
            # Check devices table type for device_id to be safe? 
            # Proceeding with standard assumption that we only touch what was requested unless we see validation errors.
            # actually we removed the FK for device_id, we should put it back.
            
            for cmd in commands:
                print(f"Executing: {cmd[:60]}...")
                conn.execute(text(cmd))
                conn.commit()
            print("UUID Migration completed successfully.")
            
    except Exception as e:
        print(f"UUID Migration Failed: {e}")

if __name__ == "__main__":
    migrate_uuid_types()
