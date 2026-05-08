#!/usr/bin/env python3
"""
Verification script to confirm the UUID fix worked
"""
import os
import sys
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def verify_schema():
    """Verify the database schema is correct"""
    try:
        # Connect to database
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL not found")
            return False
            
        # Parse DATABASE_URL for psycopg2
        import re
        match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', database_url)
        if not match:
            print("❌ Invalid DATABASE_URL format")
            return False
            
        user, password, host, port, dbname = match.groups()
        
        conn = psycopg2.connect(
            host=host, port=port, database=dbname, user=user, password=password
        )
        cursor = conn.cursor()
        
        # Check 1: Column type is now UUID
        cursor.execute("""
            SELECT data_type, udt_name 
            FROM information_schema.columns 
            WHERE table_name = 'google_sheet_triggers' 
            AND column_name = 'sheet_id'
        """)
        result = cursor.fetchone()
        
        if not result:
            print("❌ Column sheet_id not found")
            return False
            
        data_type, udt_name = result
        print(f"📋 Column type: {data_type} ({udt_name})")
        
        if data_type.lower() != 'uuid':
            print(f"❌ Column is not UUID, it's {data_type}")
            return False
            
        print("✅ Column type is correct: UUID")
        
        # Check 2: Data integrity (all valid UUIDs)
        cursor.execute("SELECT COUNT(*) FROM google_sheet_triggers")
        total_rows = cursor.fetchone()[0]
        print(f"📊 Total rows: {total_rows}")
        
        if total_rows > 0:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM google_sheet_triggers 
                WHERE sheet_id IS NULL OR sheet_id !~ '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
            """)
            invalid_count = cursor.fetchone()[0]
            
            if invalid_count > 0:
                print(f"❌ Found {invalid_count} invalid UUID values")
                return False
            else:
                print("✅ All sheet_id values are valid UUIDs")
        
        # Check 3: Sample data
        if total_rows > 0:
            cursor.execute("SELECT sheet_id FROM google_sheet_triggers LIMIT 3")
            samples = cursor.fetchall()
            print("📝 Sample UUIDs:")
            for sample in samples:
                print(f"   {sample[0]}")
        
        cursor.close()
        conn.close()
        
        print("\n🎉 Schema verification PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Verification error: {e}")
        return False

def test_query():
    """Test the problematic query that was failing"""
    try:
        database_url = os.getenv('DATABASE_URL')
        import re
        match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', database_url)
        if not match:
            return False
            
        user, password, host, port, dbname = match.groups()
        
        conn = psycopg2.connect(
            host=host, port=port, database=dbname, user=user, password=password
        )
        cursor = conn.cursor()
        
        # Test the exact query that was failing
        test_uuid = "00000000-0000-0000-0000-000000000000"  # Dummy UUID for testing
        cursor.execute("""
            SELECT COUNT(*) 
            FROM google_sheet_triggers 
            WHERE sheet_id = %s::UUID
        """, (test_uuid,))
        
        result = cursor.fetchone()[0]
        print(f"✅ Query test passed (found {result} rows for test UUID)")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Query test failed: {e}")
        return False

def main():
    print("🔍 Verifying UUID migration fix...")
    print("=" * 50)
    
    schema_ok = verify_schema()
    query_ok = test_query()
    
    print("\n" + "=" * 50)
    if schema_ok and query_ok:
        print("🎉 ALL VERIFICATIONS PASSED!")
        print("✅ The error 'operator does not exist: character varying = uuid' should be fixed")
        print("✅ FastAPI should start cleanly")
        print("✅ Google Sheets automation should run without database errors")
        return True
    else:
        print("❌ VERIFICATION FAILED!")
        print("Please check the errors above and fix them")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
