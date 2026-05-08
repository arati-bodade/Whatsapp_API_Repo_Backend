
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def migrate_single_table():
    db_url = os.getenv("DATABASE_URL")
    print(f"Using DB: {db_url[:20]}...")
    
    if "?sslmode=require" not in db_url:
        db_url += "?sslmode=require"
    
    # Use autocommit for this specific fix
    engine = create_engine(db_url)
    
    with engine.connect() as conn:
        print("Repairing master_admins.admin_id (Autocommit)...")
        
        try:
            # Drop constraint
            conn.execute(text("ALTER TABLE businesses DROP CONSTRAINT IF EXISTS businesses_parent_admin_id_fkey"))
            
            # Alter column
            conn.execute(text("ALTER TABLE master_admins ALTER COLUMN admin_id TYPE UUID USING admin_id::UUID"))
            print("Successfully altered master_admins.admin_id")
            
            # Verify immediately
            result = conn.execute(text("SELECT data_type FROM information_schema.columns WHERE table_name = 'master_admins' AND column_name = 'admin_id'"))
            for row in result:
                print(f"Verification: {row[0]}")
                
            # Re-add constraint
            # First convert the other side
            conn.execute(text("ALTER TABLE businesses ALTER COLUMN parent_admin_id TYPE UUID USING parent_admin_id::UUID"))
            conn.execute(text("ALTER TABLE businesses ADD CONSTRAINT businesses_parent_admin_id_fkey FOREIGN KEY (parent_admin_id) REFERENCES master_admins(admin_id)"))
            print("Successfully re-added FK")
            
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    migrate_single_table()
