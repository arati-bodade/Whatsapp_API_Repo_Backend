#!/usr/bin/env python3
"""
Final verification - Database schema fix complete
"""
import psycopg2
from psycopg2.extras import RealDictCursor

def final_verification():
    db_url = 'postgresql://whatsapp_patform_user:cCR4XEVKwlV3XdoOmWbGw6rdNTyBOppm@dpg-d5fp9qlactks739q3o20-a.oregon-postgres.render.com/whatsapp_patform?sslmode=require'
    
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print("🔍 FINAL VERIFICATION - Database Schema Fix")
        print("=" * 50)
        
        # Check all required columns exist
        cursor.execute("""
            SELECT column_name, data_type, column_default
            FROM information_schema.columns
            WHERE table_name = 'google_sheet_triggers'
            AND column_name IN ('status_column', 'trigger_column', 'last_processed_row')
            ORDER BY column_name
        """)
        
        columns = cursor.fetchall()
        
        required_columns = ['status_column', 'trigger_column', 'last_processed_row']
        existing_columns = [col['column_name'] for col in columns]
        
        print(f"✅ Required columns check:")
        for col in required_columns:
            if col in existing_columns:
                col_info = next(c for c in columns if c['column_name'] == col)
                print(f"   ✅ {col}: {col_info['data_type']}")
            else:
                print(f"   ❌ {col}: MISSING")
        
        # Check data integrity
        cursor.execute("""
            SELECT 
                COUNT(*) as total_triggers,
                COUNT(status_column) as with_status_column,
                COUNT(trigger_column) as with_trigger_column,
                COUNT(last_processed_row) as with_last_processed
            FROM google_sheet_triggers
        """)
        
        stats = cursor.fetchone()
        print(f"\n📊 Data Integrity:")
        print(f"   Total triggers: {stats['total_triggers']}")
        print(f"   With status_column: {stats['with_status_column']}")
        print(f"   With trigger_column: {stats['with_trigger_column']}")
        print(f"   With last_processed_row: {stats['with_last_processed']}")
        
        # Check default values
        cursor.execute("""
            SELECT DISTINCT status_column, trigger_column
            FROM google_sheet_triggers
            WHERE status_column IS NOT NULL
            LIMIT 5
        """)
        
        defaults = cursor.fetchall()
        print(f"\n🔧 Default Values (sample):")
        for row in defaults:
            print(f"   status_column: '{row['status_column']}', trigger_column: '{row['trigger_column']}'")
        
        cursor.close()
        conn.close()
        
        # Final verdict
        all_columns_exist = all(col in existing_columns for col in required_columns)
        data_integrity_ok = stats['with_status_column'] == stats['total_triggers']
        
        print(f"\n🎯 FINAL VERDICT:")
        if all_columns_exist and data_integrity_ok:
            print("   ✅ DATABASE SCHEMA FIX COMPLETE!")
            print("   ✅ All required columns exist")
            print("   ✅ Data integrity maintained")
            print("   ✅ Backend should work without errors")
            print("\n🚀 Ready for trigger creation and automation!")
        else:
            print("   ❌ Issues detected - please review")
            
        return all_columns_exist and data_integrity_ok
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

if __name__ == "__main__":
    final_verification()
