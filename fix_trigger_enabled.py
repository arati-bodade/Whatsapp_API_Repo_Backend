#!/usr/bin/env python3

from sqlalchemy import create_engine, text
from db.base import engine

def fix_trigger_enabled_column():
    """Fix trigger_enabled column to be NOT NULL with DEFAULT false"""
    
    try:
        with engine.connect() as conn:
            print("Fixing trigger_enabled column...")
            
            # Step 1: Add default value for future inserts
            print("1. Adding DEFAULT false...")
            conn.execute(text("""
                ALTER TABLE google_sheets 
                ALTER COLUMN trigger_enabled SET DEFAULT false
            """))
            
            # Step 2: Backfill existing NULL values to false
            print("2. Backfilling NULL values to false...")
            result = conn.execute(text("""
                UPDATE google_sheets 
                SET trigger_enabled = false 
                WHERE trigger_enabled IS NULL
            """))
            print(f"   Updated {result.rowcount} rows")
            
            # Step 3: Add NOT NULL constraint
            print("3. Adding NOT NULL constraint...")
            conn.execute(text("""
                ALTER TABLE google_sheets 
                ALTER COLUMN trigger_enabled SET NOT NULL
            """))
            
            conn.commit()
            print("✅ trigger_enabled column fixed successfully!")
            
            # Verify the fix
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'google_sheets' 
                AND column_name = 'trigger_enabled'
            """))
            column_info = result.fetchone()
            
            print(f"\nUpdated trigger_enabled column:")
            print(f"  name: {column_info[0]}")
            print(f"  type: {column_info[1]}")
            print(f"  nullable: {column_info[2]}")
            print(f"  default: {column_info[3]}")
                
            # Check data again
            result = conn.execute(text("""
                SELECT COUNT(*) as total_rows,
                       COUNT(trigger_enabled) as non_null_rows,
                       COUNT(*) - COUNT(trigger_enabled) as null_rows
                FROM google_sheets
            """))
            stats = result.fetchone()
            print(f"\nData statistics after fix:")
            print(f"  total rows: {stats[0]}")
            print(f"  non-null rows: {stats[1]}")
            print(f'  null rows: {stats[2]}')
                
    except Exception as e:
        print(f"❌ Error fixing column: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    fix_trigger_enabled_column()
