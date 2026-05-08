
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def migrate_operational_ids():
    db_url = os.getenv("DATABASE_URL")
    if "?sslmode=require" not in db_url:
        db_url += "?sslmode=require"
    engine = create_engine(db_url)
    
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            print("Repairing Operational Tables (UUID Conversion)...")
            
            # 1. Devices and Messages
            print("\nUpdating devices...")
            conn.execute(text("ALTER TABLE whatsapp_messages DROP CONSTRAINT IF EXISTS whatsapp_messages_device_id_fkey"))
            conn.execute(text("ALTER TABLE devices ALTER COLUMN device_id TYPE UUID USING device_id::UUID"))
            conn.execute(text("ALTER TABLE whatsapp_messages ALTER COLUMN device_id TYPE UUID USING device_id::UUID"))
            conn.execute(text("ALTER TABLE whatsapp_messages ADD CONSTRAINT whatsapp_messages_device_id_fkey FOREIGN KEY (device_id) REFERENCES devices(device_id)"))

            # 2. Campaigns
            print("\nUpdating campaigns...")
            conn.execute(text("ALTER TABLE campaigns ALTER COLUMN campaign_id TYPE UUID USING campaign_id::UUID"))
            conn.execute(text("ALTER TABLE campaigns ALTER COLUMN device_id TYPE UUID USING device_id::UUID"))

            # 3. Google Sheets and Triggers
            print("\nUpdating google_sheets and triggers...")
            conn.execute(text("ALTER TABLE google_sheet_triggers DROP CONSTRAINT IF EXISTS google_sheet_triggers_sheet_id_fkey"))
            conn.execute(text("ALTER TABLE google_sheets ALTER COLUMN sheet_id TYPE UUID USING sheet_id::UUID"))
            conn.execute(text("ALTER TABLE google_sheet_triggers ALTER COLUMN sheet_id TYPE UUID USING sheet_id::UUID"))
            conn.execute(text("ALTER TABLE google_sheet_triggers ALTER COLUMN trigger_id TYPE UUID USING trigger_id::UUID"))
            conn.execute(text("ALTER TABLE google_sheet_triggers ALTER COLUMN device_id TYPE UUID USING device_id::UUID"))
            conn.execute(text("ALTER TABLE google_sheet_triggers ADD CONSTRAINT google_sheet_triggers_sheet_id_fkey FOREIGN KEY (sheet_id) REFERENCES google_sheets(sheet_id)"))

            # 4. Message Usage and Metadata
            print("\nUpdating message_usage_credit_logs and metadata tables...")
            conn.execute(text("ALTER TABLE message_usage_credit_logs ALTER COLUMN usage_id TYPE UUID USING usage_id::UUID"))
            conn.execute(text("ALTER TABLE message_usage_credit_logs ALTER COLUMN busi_user_id TYPE UUID USING busi_user_id::UUID"))
            
            # Contact related
            conn.execute(text("ALTER TABLE contact_groups ALTER COLUMN group_id TYPE UUID USING group_id::UUID"))
            conn.execute(text("ALTER TABLE contact_groups ALTER COLUMN user_id TYPE UUID USING user_id::UUID"))
            conn.execute(text("ALTER TABLE contacts ALTER COLUMN contact_id TYPE UUID USING contact_id::UUID"))
            conn.execute(text("ALTER TABLE contacts ALTER COLUMN user_id TYPE UUID USING user_id::UUID"))

            # Audit logs
            print("\nUpdating audit_logs...")
            conn.execute(text("ALTER TABLE audit_logs ALTER COLUMN performed_by_id TYPE UUID USING performed_by_id::UUID"))
            conn.execute(text("ALTER TABLE audit_logs ALTER COLUMN affected_user_id TYPE UUID USING affected_user_id::UUID"))

            trans.commit()
            print("\nSUCCESS: ALL OPERATIONAL IDS MIGRATED SUCCESSFULLY!")
        except Exception as e:
            trans.rollback()
            print(f"\nERROR: MIGRATION FAILED: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    migrate_operational_ids()
