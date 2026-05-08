import os
import sys
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.dialects.postgresql import UUID
from dotenv import load_dotenv

# Add project root to sys.path
sys.path.append(os.getcwd())

load_dotenv()

def deep_repair_database():
    db_url = os.getenv("DATABASE_URL")
    if "?sslmode=require" not in db_url:
        db_url += "?sslmode=require"
    
    engine = create_engine(db_url)
    inspector = inspect(engine)
    
    print("--- DEEP DATABASE REPAIR INIT ---")
    
    # 1. Collect all tables
    tables = inspector.get_table_names()
    print(f"Total tables to inspect: {len(tables)}")

    # Target patterns for columns that should likely be UUIDs
    uuid_patterns = ["_id", "id_"]
    # Exact columns we know should be UUIDs
    known_uuids = {"busi_user_id", "reseller_id", "admin_id", "user_id", "plan_id", "sheet_id", "trigger_id", "device_id", "message_id", "session_id", "parent_reseller_id", "parent_admin_id", "created_by"}

    migration_commands = []

    try:
        for table in tables:
            columns = inspector.get_columns(table)
            for col in columns:
                col_name = col['name']
                col_type = str(col['type']).upper()
                
                should_be_uuid = False
                if col_name in known_uuids:
                    should_be_uuid = True
                elif any(p in col_name.lower() for p in uuid_patterns) and col_name.lower() != "mid":
                    should_be_uuid = True
                
                # If it's a known identity/linkage column but stored as VARCHAR/TEXT, migrate it!
                if should_be_uuid and ("VARCHAR" in col_type or "TEXT" in col_type):
                    print(f"  [FOUND] {table}.{col_name} is {col_type} -> migrating to UUID")
                    migration_commands.append((table, col_name))

        if not migration_commands:
            print("No new mismatches found! Schema seems healthy.")
        else:
            with engine.connect() as connection:
                connection.execution_options(isolation_level="AUTOCOMMIT")
                for table, column in migration_commands:
                    print(f"  [EXEC] Migrating {table}.{column}...")
                    try:
                        # Non-destructive cast
                        query = text(f"""
                            ALTER TABLE {table} 
                            ALTER COLUMN {column} TYPE UUID 
                            USING {column}::UUID
                        """)
                        connection.execute(query)
                        # print(f"  [OK] Done.")
                    except Exception as e:
                        if "already exists" in str(e).lower(): continue
                        print(f"  [ERROR] Failed {table}.{column}: {e}")

        # 2. Sync Enums
        print("\n2. Re-Syncing Enums...")
        enum_updates = {
            "devicetype": ["WEB", "MOBILE", "DESKTOP", "OFFICIAL", "web", "mobile", "desktop", "official"],
            "sessionstatus": ["CONNECTED", "DISCONNECTED", "QR_GENERATED", "PENDING", "connected", "disconnected", "qr_generated", "pending"],
            "messagetype": ["OTP", "TEXT", "TEMPLATE", "MEDIA", "BASE64"],
            "messagestatus": ["PENDING", "SENT", "DELIVERED", "READ", "FAILED"],
            "campaignstatus": ["PENDING", "RUNNING", "PAUSED", "COMPLETED", "FAILED"],
            "sheetstatus": ["ACTIVE", "PAUSED", "ERROR"]
        }
        with engine.connect() as connection:
            connection.execution_options(isolation_level="AUTOCOMMIT")
            for enum_name, values in enum_updates.items():
                for val in values:
                    try:
                        connection.execute(text(f"ALTER TYPE {enum_name} ADD VALUE IF NOT EXISTS '{val}'"))
                    except: pass

        print("\nFINISHED: REPAIR CYCLE COMPLETE!")

    except Exception as e:
        print(f"CRITICAL: {e}")

if __name__ == "__main__":
    deep_repair_database()
