
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def migrate_remaining():
    db_url = os.getenv("DATABASE_URL")
    if "?sslmode=require" not in db_url:
        db_url += "?sslmode=require"
    engine = create_engine(db_url)
    
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            print("Repairing Remaining Tables (UUID Conversion)...")
            
            # 1. Devices and Messages
            print("\nUpdating devices and whatsapp_messages...")
            try:
                conn.execute(text("ALTER TABLE whatsapp_messages DROP CONSTRAINT IF EXISTS whatsapp_messages_device_id_fkey"))
            except: pass
            conn.execute(text("ALTER TABLE devices ALTER COLUMN device_id TYPE UUID USING device_id::UUID"))
            conn.execute(text("ALTER TABLE whatsapp_messages ALTER COLUMN device_id TYPE UUID USING device_id::UUID"))
            try:
                conn.execute(text("ALTER TABLE whatsapp_messages ADD CONSTRAINT whatsapp_messages_device_id_fkey FOREIGN KEY (device_id) REFERENCES devices(device_id)"))
            except: pass

            # 2. Campaigns
            print("\nUpdating campaigns...")
            conn.execute(text("ALTER TABLE campaigns ALTER COLUMN id TYPE UUID USING id::UUID"))
            conn.execute(text("ALTER TABLE campaigns ALTER COLUMN busi_user_id TYPE UUID USING busi_user_id::UUID"))

            # 3. Google Sheets and Triggers
            print("\nUpdating google_sheets and google_sheet_triggers...")
            try:
                conn.execute(text("ALTER TABLE google_sheet_triggers DROP CONSTRAINT IF EXISTS google_sheet_triggers_sheet_id_fkey"))
            except: pass
            
            conn.execute(text("ALTER TABLE google_sheets ALTER COLUMN id TYPE UUID USING id::UUID"))
            conn.execute(text("ALTER TABLE google_sheets ALTER COLUMN user_id TYPE UUID USING user_id::UUID"))
            
            conn.execute(text("ALTER TABLE google_sheet_triggers ALTER COLUMN trigger_id TYPE UUID USING trigger_id::UUID"))
            conn.execute(text("ALTER TABLE google_sheet_triggers ALTER COLUMN sheet_id TYPE UUID USING sheet_id::UUID"))
            conn.execute(text("ALTER TABLE google_sheet_triggers ALTER COLUMN device_id TYPE UUID USING device_id::UUID"))
            conn.execute(text("ALTER TABLE google_sheet_triggers ALTER COLUMN user_id TYPE UUID USING user_id::UUID"))
            
            try:
                conn.execute(text("ALTER TABLE google_sheet_triggers ADD CONSTRAINT google_sheet_triggers_sheet_id_fkey FOREIGN KEY (sheet_id) REFERENCES google_sheets(id)"))
            except: pass

            # 4. Message Usage
            print("\nUpdating message_usage_credit_logs...")
            conn.execute(text("ALTER TABLE message_usage_credit_logs ALTER COLUMN usage_id TYPE UUID USING usage_id::UUID"))
            conn.execute(text("ALTER TABLE message_usage_credit_logs ALTER COLUMN busi_user_id TYPE UUID USING busi_user_id::UUID"))

            # 5. Audit logs
            print("\nUpdating audit_logs...")
            conn.execute(text("ALTER TABLE audit_logs ALTER COLUMN log_id TYPE UUID USING log_id::UUID"))
            conn.execute(text("ALTER TABLE audit_logs ALTER COLUMN performed_by_id TYPE UUID USING performed_by_id::UUID"))
            conn.execute(text("ALTER TABLE audit_logs ALTER COLUMN affected_user_id TYPE UUID USING affected_user_id::UUID"))
            conn.execute(text("ALTER TABLE audit_logs ALTER COLUMN reseller_id TYPE UUID USING reseller_id::UUID"))

            # 6. Contact tables
            print("\nUpdating contact tables...")
            try:
                conn.execute(text("ALTER TABLE contact_groups ALTER COLUMN group_id TYPE UUID USING group_id::UUID"))
                conn.execute(text("ALTER TABLE contact_groups ALTER COLUMN user_id TYPE UUID USING user_id::UUID"))
                conn.execute(text("ALTER TABLE contacts ALTER COLUMN contact_id TYPE UUID USING contact_id::UUID"))
                conn.execute(text("ALTER TABLE contacts ALTER COLUMN user_id TYPE UUID USING user_id::UUID"))
            except Exception as e:
                print(f"Warning on contact tables: {e}")

            trans.commit()
            print("\nSUCCESS: ALL REMAINING TABLES MIGRATED SUCCESSFULLY!")
        except Exception as e:
            trans.rollback()
            print(f"\nERROR: MIGRATION FAILED: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    migrate_remaining()
