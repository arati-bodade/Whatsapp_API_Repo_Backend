import sys
import os
from sqlalchemy import text

# Add the current directory to sys.path
sys.path.append(os.getcwd())

from db.base import engine
from db.init_db import init_db

def force_reinitialize():
    print("Starting AGGRESSIVE database reinitialization...")
    db_name = "whatsapp_platform_mhnw"
    
    try:
        with engine.connect() as conn:
            # 1. Kill all other connections to the database
            print("Terminating other connections...")
            conn.execute(text(f"""
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = '{db_name}' AND pid <> pg_backend_pid();
            """))
            conn.commit()
            
            # 2. Drop and recreate schema
            print("Purging public schema...")
            conn.execute(text("""
                DROP SCHEMA public CASCADE;
                CREATE SCHEMA public;
                GRANT ALL ON SCHEMA public TO public;
                GRANT ALL ON SCHEMA public TO whatsapp_platform_mhnw_user;
            """))
            conn.commit()
            
        # 3. Re-initialize tables
        print("Recreating tables...")
        init_db()
        print("Aggressive reinitialization SUCCESSFUL!")
        
    except Exception as e:
        print(f"❌ Aggressive reinitialization FAILED: {e}")

if __name__ == "__main__":
    force_reinitialize()
