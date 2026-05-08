#!/usr/bin/env python3
"""
Clean database - Full device reset
"""
import psycopg2

def clean_database():
    db_url = 'postgresql://whatsapp_patform_user:cCR4XEVKwlV3XdoOmWbGw6rdNTyBOppm@dpg-d5fp9qlactks739q3o20-a.oregon-postgres.render.com/whatsapp_patform?sslmode=require'
    
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        print("🧹 CLEANING DATABASE - FULL DEVICE RESET")
        print("=" * 50)
        
        # Check counts before deletion
        cursor.execute("SELECT COUNT(*) FROM devices")
        device_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM google_sheet_triggers")
        trigger_count = cursor.fetchone()[0]
        
        print(f"📊 Before cleanup:")
        print(f"   Devices: {device_count}")
        print(f"   Triggers: {trigger_count}")
        
        # Delete triggers first (foreign key constraint)
        cursor.execute("DELETE FROM google_sheet_triggers")
        triggers_deleted = cursor.rowcount
        
        # Delete devices
        cursor.execute("DELETE FROM devices")
        devices_deleted = cursor.rowcount
        
        conn.commit()
        
        print(f"\n✅ Cleanup complete:")
        print(f"   Triggers deleted: {triggers_deleted}")
        print(f"   Devices deleted: {devices_deleted}")
        
        # Verify cleanup
        cursor.execute("SELECT COUNT(*) FROM devices")
        device_count_after = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM google_sheet_triggers")
        trigger_count_after = cursor.fetchone()[0]
        
        print(f"\n📊 After cleanup:")
        print(f"   Devices: {device_count_after}")
        print(f"   Triggers: {trigger_count_after}")
        
        cursor.close()
        conn.close()
        
        return device_count_after == 0 and trigger_count_after == 0
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

if __name__ == "__main__":
    clean_database()
