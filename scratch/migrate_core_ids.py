
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def migrate_core_ids():
    db_url = os.getenv("DATABASE_URL")
    if "?sslmode=require" not in db_url:
        db_url += "?sslmode=require"
    engine = create_engine(db_url)
    
    with engine.connect() as conn:
        # 1. Start session
        conn.execute(text("BEGIN;"))
        try:
            print("Repairing master_admins.admin_id...")
            
            # Since master_admins.admin_id is a Primary Key, we need to check if any FKs point to it.
            # businesses.parent_admin_id points to it.
            
            print("  Dropping FK businesses_parent_admin_id_fkey...")
            try:
                conn.execute(text("ALTER TABLE businesses DROP CONSTRAINT IF EXISTS businesses_parent_admin_id_fkey"))
            except Exception as e:
                print(f"  Warning: {e}")

            print("  Converting master_admins.admin_id to UUID...")
            conn.execute(text("ALTER TABLE master_admins ALTER COLUMN admin_id TYPE UUID USING admin_id::UUID"))
            
            print("  Converting businesses.parent_admin_id to UUID...")
            conn.execute(text("ALTER TABLE businesses ALTER COLUMN parent_admin_id TYPE UUID USING parent_admin_id::UUID"))
            
            print("  Re-adding FK businesses_parent_admin_id_fkey...")
            conn.execute(text("ALTER TABLE businesses ADD CONSTRAINT businesses_parent_admin_id_fkey FOREIGN KEY (parent_admin_id) REFERENCES master_admins(admin_id)"))

            # 2. Fix Resellers and Business Users
            print("\nRepairing resellers and businesses PKs...")
            
            # Drop dependencies on resellers.reseller_id
            print("  Dropping FKs on resellers...")
            conn.execute(text("ALTER TABLE businesses DROP CONSTRAINT IF EXISTS businesses_parent_reseller_id_fkey"))
            
            print("  Converting resellers.reseller_id to UUID...")
            conn.execute(text("ALTER TABLE resellers ALTER COLUMN reseller_id TYPE UUID USING reseller_id::UUID"))
            
            print("  Converting businesses.parent_reseller_id to UUID...")
            conn.execute(text("ALTER TABLE businesses ALTER COLUMN parent_reseller_id TYPE UUID USING parent_reseller_id::UUID"))
            
            print("  Re-adding FK businesses_parent_reseller_id_fkey...")
            conn.execute(text("ALTER TABLE businesses ADD CONSTRAINT businesses_parent_reseller_id_fkey FOREIGN KEY (parent_reseller_id) REFERENCES resellers(reseller_id)"))

            # Fix businesses.busi_user_id (Primary Key)
            print("\nRepairing businesses.busi_user_id...")
            # Drop dependencies on businesses.busi_user_id
            print("  Dropping FKs on businesses...")
            conn.execute(text("ALTER TABLE devices DROP CONSTRAINT IF EXISTS devices_busi_user_id_fkey"))
            conn.execute(text("ALTER TABLE campaigns DROP CONSTRAINT IF EXISTS campaigns_busi_user_id_fkey"))
            conn.execute(text("ALTER TABLE google_sheets DROP CONSTRAINT IF EXISTS google_sheets_user_id_fkey"))
            
            print("  Converting businesses.busi_user_id to UUID...")
            conn.execute(text("ALTER TABLE businesses ALTER COLUMN busi_user_id TYPE UUID USING busi_user_id::UUID"))
            
            print("  Converting devices.busi_user_id to UUID...")
            conn.execute(text("ALTER TABLE devices ALTER COLUMN busi_user_id TYPE UUID USING busi_user_id::UUID"))
            
            print("  Converting campaigns.busi_user_id to UUID...")
            conn.execute(text("ALTER TABLE campaigns ALTER COLUMN busi_user_id TYPE UUID USING busi_user_id::UUID"))
            
            print("  Converting google_sheets.user_id to UUID...")
            conn.execute(text("ALTER TABLE google_sheets ALTER COLUMN user_id TYPE UUID USING user_id::UUID"))
            
            print("  Re-adding FKs on businesses...")
            conn.execute(text("ALTER TABLE devices ADD CONSTRAINT devices_busi_user_id_fkey FOREIGN KEY (busi_user_id) REFERENCES businesses(busi_user_id)"))
            conn.execute(text("ALTER TABLE campaigns ADD CONSTRAINT campaigns_busi_user_id_fkey FOREIGN KEY (busi_user_id) REFERENCES businesses(busi_user_id)"))
            conn.execute(text("ALTER TABLE google_sheets ADD CONSTRAINT google_sheets_user_id_fkey FOREIGN KEY (user_id) REFERENCES businesses(busi_user_id)"))
            
            conn.execute(text("COMMIT;"))
            print("\n✅ CORE IDS MIGRATED SUCCESSFULLY!")
        except Exception as e:
            conn.execute(text("ROLLBACK;"))
            print(f"\n❌ MIGRATION FAILED: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    migrate_core_ids()
