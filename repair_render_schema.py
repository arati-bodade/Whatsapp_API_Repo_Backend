import os
import sys
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv

# Add project root to sys.path
sys.path.append(os.getcwd())

load_dotenv()

def repair_database():
    db_url = os.getenv("DATABASE_URL")
    if "?sslmode=require" not in db_url:
        db_url += "?sslmode=require"
    
    engine = create_engine(db_url)
    
    try:
        with engine.connect() as connection:
            connection.execution_options(isolation_level="AUTOCOMMIT")
            print("--- RENDER DATABASE REPAIR TOOL ---")

            # --- PART 1: Sync Enums (Safe Case Normalization) ---
            print("\n1. Syncing Enums (Adding Uppercase support)...")
            enum_updates = {
                "devicetype": ["WEB", "MOBILE", "DESKTOP", "OFFICIAL", "web", "mobile", "desktop", "official"],
                "sessionstatus": ["CONNECTED", "DISCONNECTED", "QR_GENERATED", "PENDING", "connected", "disconnected", "qr_generated", "pending"],
                "messagetype": ["OTP", "TEXT", "TEMPLATE", "MEDIA", "BASE64"],
                "messagestatus": ["PENDING", "SENT", "DELIVERED", "READ", "FAILED"],
                "campaignstatus": ["PENDING", "RUNNING", "PAUSED", "COMPLETED", "FAILED"],
                "channeltype": ["WHATSAPP", "whatsapp"]
            }
            
            for enum_name, values in enum_updates.items():
                print(f" Checking enum: {enum_name}")
                for val in values:
                    try:
                        connection.execute(text(f"ALTER TYPE {enum_name} ADD VALUE IF NOT EXISTS '{val}'"))
                    except Exception as e:
                        if "already exists" not in str(e).lower():
                            print(f"  Warning: {val} -> {e}")

            # --- PART 2: Convert VARCHAR IDs to UUIDs ---
            print("\n2. Repairing UUID Type Mismatches...")
            
            # List of (Table, Column) pairs known to be problematic based on logs
            tables_to_fix = [
                ("devices", "busi_user_id"),
                ("google_sheets", "user_id"),
                ("google_sheet_triggers", "sheet_id"),
                ("businesses", "busi_user_id"),
                ("resellers", "reseller_id"),
                ("audit_logs", "affected_user_id"),
                ("audit_logs", "performed_by_id"),
                ("credit_distributions", "to_business_user_id"),
                ("credit_distributions", "from_admin_id"),
                ("campaigns", "busi_user_id")
            ]
            
            inspector = inspect(engine)
            
            for table, column in tables_to_fix:
                print(f" Checking {table}.{column}...")
                try:
                    columns = inspector.get_columns(table)
                    col_info = next((c for c in columns if c['name'] == column), None)
                    
                    if col_info and 'VARCHAR' in str(col_info['type']).upper():
                        print(f"  WARN: Converting {table}.{column} from VARCHAR to UUID...")
                        
                        # Apply transformation
                        query = text(f"""
                            ALTER TABLE {table} 
                            ALTER COLUMN {column} TYPE UUID 
                            USING {column}::UUID
                        """)
                        connection.execute(query)
                        print(f"  SUCCESS: Fixed {table}.{column}")
                    else:
                        print(f"  INFO: {table}.{column} is already correct or missing.")
                except Exception as e:
                    print(f"  ERROR: Error fixing {table}.{column}: {e}")

            # --- PART 3: Data Integrity ---
            print("\n3. Repairing Data Logic Linkage...")
            try:
                # Fix orphaned devices - link them to our main test user
                fix_query = text("""
                    UPDATE devices 
                    SET busi_user_id = (SELECT busi_user_id FROM businesses WHERE email = 'lungeom39@gmail.com' LIMIT 1)
                    WHERE busi_user_id NOT IN (SELECT busi_user_id FROM businesses);
                """)
                res = connection.execute(fix_query)
                print(f" SUCCESS: Relinked {res.rowcount} orphaned device(s).")
            except Exception as e:
                 print(f" ERROR: Linkage fix failed: {e}")

            print("\nFINISHED: ALL REPAIRS COMPLETE!")

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")

if __name__ == "__main__":
    repair_database()
