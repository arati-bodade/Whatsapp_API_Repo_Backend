import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def sync_enums():
    db_url = os.getenv("DATABASE_URL")
    if "?sslmode=require" not in db_url:
        db_url += "?sslmode=require"
    
    engine = create_engine(db_url)
    
    # List of Enum types and the values we want to ensure exist (supporting both cases)
    enum_updates = {
        "devicetype": ["WEB", "MOBILE", "DESKTOP", "OFFICIAL", "web", "mobile", "desktop", "official"],
        "sessionstatus": ["CONNECTED", "DISCONNECTED", "QR_GENERATED", "PENDING", "connected", "disconnected", "qr_generated", "pending"],
        "messagetype": ["OTP", "TEXT", "TEMPLATE", "MEDIA", "BASE64"],
        "messagestatus": ["PENDING", "SENT", "DELIVERED", "READ", "FAILED"],
        "campaignstatus": ["PENDING", "RUNNING", "PAUSED", "COMPLETED", "FAILED"]
    }
    
    try:
        with engine.connect() as connection:
            # We must use transactional isolation for some enum operations in PG
            # But ALTER TYPE ... ADD VALUE cannot be run inside a transaction block in some versions
            connection.execution_options(isolation_level="AUTOCOMMIT")
            
            print("🚀 Starting Non-Destructive Enum Synchronization on Render...")
            
            for enum_name, values in enum_updates.items():
                print(f"Syncing {enum_name}...")
                for val in values:
                    try:
                        # PostgreSQL syntax for adding enum values safely
                        query = text(f"ALTER TYPE {enum_name} ADD VALUE IF NOT EXISTS '{val}'")
                        connection.execute(query)
                        # print(f"  - Ensuring '{val}' exists")
                    except Exception as e:
                        # Some PG versions don't support IF NOT EXISTS with ALTER TYPE
                        # In that case we just catch the "already exists" error
                        if "already exists" in str(e).lower():
                            continue
                        else:
                            print(f"  - Warning for '{val}': {e}")
            
            print("\n✅ Enum Synchronization Complete!")
            
            # --- Bonus: Fix the orphaned device record ---
            print("\n🛠️ Fixing Data Linkage (Linking orphaned device to Om Lunge)...")
            fix_linkage_query = text("""
                UPDATE devices 
                SET busi_user_id = (SELECT busi_user_id FROM businesses WHERE email = 'lungeom39@gmail.com' LIMIT 1)
                WHERE busi_user_id NOT IN (SELECT busi_user_id FROM businesses);
            """)
            result = connection.execute(fix_linkage_query)
            print(f"✅ Repaired {result.rowcount} device record(s).")

    except Exception as e:
        print(f"❌ Synchronization failed: {e}")

if __name__ == "__main__":
    sync_enums()
