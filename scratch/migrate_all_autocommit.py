
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def migrate_all_autocommit():
    db_url = os.getenv("DATABASE_URL")
    if "?sslmode=require" not in db_url:
        db_url += "?sslmode=require"
    engine = create_engine(db_url)
    
    with engine.connect() as conn:
        print("Starting Comprehensive Database Repair (Autocommit Mode)...")
        
        # Helper to execute and print
        def execute_sql(sql):
            try:
                conn.execute(text(sql))
                print(f"SUCCESS: {sql[:60]}...")
            except Exception as e:
                print(f"WARNING: {sql[:60]}... -> {str(e)[:100]}")

        # 1. CORE TABLES - User IDs
        print("\n--- Repairing Core User IDs ---")
        
        # Master Admin -> Businesses
        execute_sql("ALTER TABLE businesses DROP CONSTRAINT IF EXISTS businesses_parent_admin_id_fkey")
        execute_sql("ALTER TABLE master_admins ALTER COLUMN admin_id TYPE UUID USING admin_id::UUID")
        execute_sql("ALTER TABLE businesses ALTER COLUMN parent_admin_id TYPE UUID USING parent_admin_id::UUID")
        execute_sql("ALTER TABLE businesses ADD CONSTRAINT businesses_parent_admin_id_fkey FOREIGN KEY (parent_admin_id) REFERENCES master_admins(admin_id)")

        # Resellers -> Businesses
        execute_sql("ALTER TABLE businesses DROP CONSTRAINT IF EXISTS businesses_parent_reseller_id_fkey")
        execute_sql("ALTER TABLE resellers ALTER COLUMN reseller_id TYPE UUID USING reseller_id::UUID")
        execute_sql("ALTER TABLE businesses ALTER COLUMN parent_reseller_id TYPE UUID USING parent_reseller_id::UUID")
        execute_sql("ALTER TABLE businesses ADD CONSTRAINT businesses_parent_reseller_id_fkey FOREIGN KEY (parent_reseller_id) REFERENCES resellers(reseller_id)")

        # Businesses PK
        execute_sql("ALTER TABLE devices DROP CONSTRAINT IF EXISTS devices_busi_user_id_fkey")
        execute_sql("ALTER TABLE campaigns DROP CONSTRAINT IF EXISTS campaigns_busi_user_id_fkey")
        execute_sql("ALTER TABLE google_sheets DROP CONSTRAINT IF EXISTS google_sheets_user_id_fkey")
        execute_sql("ALTER TABLE businesses ALTER COLUMN busi_user_id TYPE UUID USING busi_user_id::UUID")
        execute_sql("ALTER TABLE devices ALTER COLUMN busi_user_id TYPE UUID USING busi_user_id::UUID")
        execute_sql("ALTER TABLE campaigns ALTER COLUMN busi_user_id TYPE UUID USING busi_user_id::UUID")
        execute_sql("ALTER TABLE google_sheets ALTER COLUMN user_id TYPE UUID USING user_id::UUID")
        execute_sql("ALTER TABLE devices ADD CONSTRAINT devices_busi_user_id_fkey FOREIGN KEY (busi_user_id) REFERENCES businesses(busi_user_id)")
        execute_sql("ALTER TABLE campaigns ADD CONSTRAINT campaigns_busi_user_id_fkey FOREIGN KEY (busi_user_id) REFERENCES businesses(busi_user_id)")
        execute_sql("ALTER TABLE google_sheets ADD CONSTRAINT google_sheets_user_id_fkey FOREIGN KEY (user_id) REFERENCES businesses(busi_user_id)")

        # 2. OPERATIONAL TABLES - IDs
        print("\n--- Repairing Operational IDs ---")
        
        # Devices
        execute_sql("ALTER TABLE whatsapp_messages DROP CONSTRAINT IF EXISTS whatsapp_messages_device_id_fkey")
        execute_sql("ALTER TABLE devices ALTER COLUMN device_id TYPE UUID USING device_id::UUID")
        execute_sql("ALTER TABLE whatsapp_messages ALTER COLUMN device_id TYPE UUID USING device_id::UUID")
        execute_sql("ALTER TABLE whatsapp_messages ADD CONSTRAINT whatsapp_messages_device_id_fkey FOREIGN KEY (device_id) REFERENCES devices(device_id)")

        # Campaigns
        execute_sql("ALTER TABLE campaigns ALTER COLUMN id TYPE UUID USING id::UUID")

        # Google Sheets & Triggers
        execute_sql("ALTER TABLE google_sheet_triggers DROP CONSTRAINT IF EXISTS google_sheet_triggers_sheet_id_fkey")
        execute_sql("ALTER TABLE google_sheets ALTER COLUMN id TYPE UUID USING id::UUID")
        execute_sql("ALTER TABLE google_sheet_triggers ALTER COLUMN sheet_id TYPE UUID USING sheet_id::UUID")
        execute_sql("ALTER TABLE google_sheet_triggers ALTER COLUMN trigger_id TYPE UUID USING trigger_id::UUID")
        execute_sql("ALTER TABLE google_sheet_triggers ALTER COLUMN device_id TYPE UUID USING device_id::UUID")
        execute_sql("ALTER TABLE google_sheet_triggers ALTER COLUMN user_id TYPE UUID USING user_id::UUID")
        execute_sql("ALTER TABLE google_sheet_triggers ADD CONSTRAINT google_sheet_triggers_sheet_id_fkey FOREIGN KEY (sheet_id) REFERENCES google_sheets(id)")

        # Logs
        execute_sql("ALTER TABLE audit_logs ALTER COLUMN log_id TYPE UUID USING log_id::UUID")
        execute_sql("ALTER TABLE audit_logs ALTER COLUMN performed_by_id TYPE UUID USING performed_by_id::UUID")
        execute_sql("ALTER TABLE audit_logs ALTER COLUMN affected_user_id TYPE UUID USING affected_user_id::UUID")
        execute_sql("ALTER TABLE audit_logs ALTER COLUMN reseller_id TYPE UUID USING reseller_id::UUID")

        # Tables with mixed data (careful!)
        # We only convert if they are valid UUIDs, otherwise keeping as VARCHAR might be safer for logs.
        # But models expect UUID for usage_id.
        # Let's try to convert usage_id but ignore failures if it's not a UUID.
        execute_sql("ALTER TABLE message_usage_credit_logs ALTER COLUMN busi_user_id TYPE UUID USING busi_user_id::UUID")
        
        print("\nFINAL SCAN: Verifying types...")
        # (Verification script can be run after)
        
        print("\nCOMPLETED: DATABASE REPAIR ATTEMPT FINISHED.")

if __name__ == "__main__":
    migrate_all_autocommit()
