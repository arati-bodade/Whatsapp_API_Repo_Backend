
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def migrate_and_verify():
    db_url = os.getenv("DATABASE_URL")
    if "?sslmode=require" not in db_url:
        db_url += "?sslmode=require"
    engine = create_engine(db_url)
    
    with engine.connect() as conn:
        print("Starting FINAL Database Repair (Autocommit Mode)...")
        
        commands = [
            # Master Admin
            "ALTER TABLE businesses DROP CONSTRAINT IF EXISTS businesses_parent_admin_id_fkey",
            "ALTER TABLE master_admins ALTER COLUMN admin_id TYPE UUID USING admin_id::UUID",
            "ALTER TABLE businesses ALTER COLUMN parent_admin_id TYPE UUID USING parent_admin_id::UUID",
            "ALTER TABLE businesses ADD CONSTRAINT businesses_parent_admin_id_fkey FOREIGN KEY (parent_admin_id) REFERENCES master_admins(admin_id)",
            
            # Resellers
            "ALTER TABLE businesses DROP CONSTRAINT IF EXISTS businesses_parent_reseller_id_fkey",
            "ALTER TABLE resellers ALTER COLUMN reseller_id TYPE UUID USING reseller_id::UUID",
            "ALTER TABLE businesses ALTER COLUMN parent_reseller_id TYPE UUID USING parent_reseller_id::UUID",
            "ALTER TABLE businesses ADD CONSTRAINT businesses_parent_reseller_id_fkey FOREIGN KEY (parent_reseller_id) REFERENCES resellers(reseller_id)",
            
            # Businesses
            "ALTER TABLE devices DROP CONSTRAINT IF EXISTS devices_busi_user_id_fkey",
            "ALTER TABLE campaigns DROP CONSTRAINT IF EXISTS campaigns_busi_user_id_fkey",
            "ALTER TABLE google_sheets DROP CONSTRAINT IF EXISTS google_sheets_user_id_fkey",
            "ALTER TABLE businesses ALTER COLUMN busi_user_id TYPE UUID USING busi_user_id::UUID",
            "ALTER TABLE devices ALTER COLUMN busi_user_id TYPE UUID USING busi_user_id::UUID",
            "ALTER TABLE campaigns ALTER COLUMN busi_user_id TYPE UUID USING busi_user_id::UUID",
            "ALTER TABLE google_sheets ALTER COLUMN user_id TYPE UUID USING user_id::UUID",
            "ALTER TABLE devices ADD CONSTRAINT devices_busi_user_id_fkey FOREIGN KEY (busi_user_id) REFERENCES businesses(busi_user_id)",
            "ALTER TABLE campaigns ADD CONSTRAINT campaigns_busi_user_id_fkey FOREIGN KEY (busi_user_id) REFERENCES businesses(busi_user_id)",
            "ALTER TABLE google_sheets ADD CONSTRAINT google_sheets_user_id_fkey FOREIGN KEY (user_id) REFERENCES businesses(busi_user_id)",
            
            # Devices
            "ALTER TABLE whatsapp_messages DROP CONSTRAINT IF EXISTS whatsapp_messages_device_id_fkey",
            "ALTER TABLE devices ALTER COLUMN device_id TYPE UUID USING device_id::UUID",
            "ALTER TABLE whatsapp_messages ALTER COLUMN device_id TYPE UUID USING device_id::UUID",
            "ALTER TABLE whatsapp_messages ADD CONSTRAINT whatsapp_messages_device_id_fkey FOREIGN KEY (device_id) REFERENCES devices(device_id)",
            
            # Others
            "ALTER TABLE campaigns ALTER COLUMN id TYPE UUID USING id::UUID",
            "ALTER TABLE google_sheets ALTER COLUMN id TYPE UUID USING id::UUID",
            "ALTER TABLE google_sheet_triggers ALTER COLUMN trigger_id TYPE UUID USING trigger_id::UUID",
            "ALTER TABLE google_sheet_triggers ALTER COLUMN sheet_id TYPE UUID USING sheet_id::UUID",
            "ALTER TABLE google_sheet_triggers ALTER COLUMN device_id TYPE UUID USING device_id::UUID",
            "ALTER TABLE google_sheet_triggers ALTER COLUMN user_id TYPE UUID USING user_id::UUID",
            "ALTER TABLE audit_logs ALTER COLUMN log_id TYPE UUID USING log_id::UUID",
            "ALTER TABLE audit_logs ALTER COLUMN performed_by_id TYPE UUID USING performed_by_id::UUID",
            "ALTER TABLE audit_logs ALTER COLUMN affected_user_id TYPE UUID USING affected_user_id::UUID"
        ]
        
        for cmd in commands:
            try:
                conn.execute(text(cmd))
                print(f"OK: {cmd[:50]}...")
            except Exception as e:
                print(f"SKIP/FAIL: {cmd[:50]}... -> {str(e)[:100]}")
        
        print("\nVerifying...")
        tables = ['master_admins', 'resellers', 'businesses', 'devices', 'campaigns', 'google_sheets', 'google_sheet_triggers']
        for table in tables:
            res = conn.execute(text(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}' AND (column_name LIKE '%_id' OR column_name = 'id' OR column_name = 'admin_id')"))
            for row in res:
                print(f"{table}.{row[0]}: {row[1]}")

if __name__ == "__main__":
    migrate_and_verify()
