import sys
import os
from sqlalchemy import create_engine, text

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.config import settings

def fix_database():
    print("🔌 Connecting to database...")
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as connection:
        print("🛠️ Attempting to add missing columns...")
        
        # 1. generated_at
        try:
            connection.execute(text("""
                ALTER TABLE business_user_analytics 
                ADD COLUMN IF NOT EXISTS generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL;
            """))
            print("   ✅ Added 'generated_at' column (or it already existed).")
        except Exception as e:
            print(f"   ⚠️ Error adding 'generated_at': {e}")

        # 2. updated_at
        try:
            connection.execute(text("""
                ALTER TABLE business_user_analytics 
                ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL;
            """))
            print("   ✅ Added 'updated_at' column (or it already existed).")
        except Exception as e:
            print(f"   ⚠️ Error adding 'updated_at': {e}")
            
        connection.commit()
        print("🏁 Database fix complete.")

if __name__ == "__main__":
    fix_database()
