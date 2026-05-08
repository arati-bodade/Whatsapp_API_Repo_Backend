
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def migrate_robustly():
    db_url = os.getenv("DATABASE_URL")
    if "?sslmode=require" not in db_url:
        db_url += "?sslmode=require"
    engine = create_engine(db_url)
    
    steps = [
         # Fix Master Admin -> Businesses link
        ("businesses_parent_admin_id_fkey", "ALTER TABLE businesses DROP CONSTRAINT IF EXISTS businesses_parent_admin_id_fkey"),
        ("master_admins.admin_id", "ALTER TABLE master_admins ALTER COLUMN admin_id TYPE UUID USING admin_id::UUID"),
        ("businesses.parent_admin_id", "ALTER TABLE businesses ALTER COLUMN parent_admin_id TYPE UUID USING parent_admin_id::UUID"),
        ("RE-ADD fkey_admin", "ALTER TABLE businesses ADD CONSTRAINT businesses_parent_admin_id_fkey FOREIGN KEY (parent_admin_id) REFERENCES master_admins(admin_id)"),

        # Fix Reseller -> Businesses link
        ("businesses_parent_reseller_id_fkey", "ALTER TABLE businesses DROP CONSTRAINT IF EXISTS businesses_parent_reseller_id_fkey"),
        ("resellers.reseller_id", "ALTER TABLE resellers ALTER COLUMN reseller_id TYPE UUID USING reseller_id::UUID"),
        ("businesses.parent_reseller_id", "ALTER TABLE businesses ALTER COLUMN parent_reseller_id TYPE UUID USING parent_reseller_id::UUID"),
        ("RE-ADD fkey_reseller", "ALTER TABLE businesses ADD CONSTRAINT businesses_parent_reseller_id_fkey FOREIGN KEY (parent_reseller_id) REFERENCES resellers(reseller_id)"),

        # Fix Businesses PK and its dependents
        ("businesses.busi_user_id (PK)", "ALTER TABLE businesses ALTER COLUMN busi_user_id TYPE UUID USING busi_user_id::UUID"),
        ("devices.busi_user_id (FK)", "ALTER TABLE devices ALTER COLUMN busi_user_id TYPE UUID USING busi_user_id::UUID"),
        ("campaigns.busi_user_id (FK)", "ALTER TABLE campaigns ALTER COLUMN busi_user_id TYPE UUID USING busi_user_id::UUID"),
        ("google_sheets.user_id (FK)", "ALTER TABLE google_sheets ALTER COLUMN user_id TYPE UUID USING user_id::UUID"),
        
        # Operational
        ("devices.device_id (PK)", "ALTER TABLE devices ALTER COLUMN device_id TYPE UUID USING device_id::UUID"),
        ("whatsapp_messages.device_id (FK)", "ALTER TABLE whatsapp_messages ALTER COLUMN device_id TYPE UUID USING device_id::UUID"),
        ("campaigns.id (PK)", "ALTER TABLE campaigns ALTER COLUMN id TYPE UUID USING id::UUID"),
        ("google_sheets.id (PK)", "ALTER TABLE google_sheets ALTER COLUMN id TYPE UUID USING id::UUID"),
        ("google_sheet_triggers.trigger_id (PK)", "ALTER TABLE google_sheet_triggers ALTER COLUMN trigger_id TYPE UUID USING trigger_id::UUID"),
        ("google_sheet_triggers.sheet_id (FK)", "ALTER TABLE google_sheet_triggers ALTER COLUMN sheet_id TYPE UUID USING sheet_id::UUID"),
        ("google_sheet_triggers.device_id (FK)", "ALTER TABLE google_sheet_triggers ALTER COLUMN device_id TYPE UUID USING device_id::UUID"),
        ("google_sheet_triggers.user_id (FK)", "ALTER TABLE google_sheet_triggers ALTER COLUMN user_id TYPE UUID USING user_id::UUID")
    ]
    
    with engine.connect() as conn:
        for desc, sql in steps:
            try:
                # Use separate transaction for each step to avoid state corruption
                with conn.begin():
                    conn.execute(text(sql))
                    print(f"✅ {desc} COMPLETED")
            except Exception as e:
                print(f"❌ {desc} FAILED: {str(e)[:150]}")

if __name__ == "__main__":
    migrate_robustly()
