#!/usr/bin/env python3
"""
🔥 STEP 2: FIX DEVICE OWNERSHIP (MOST IMPORTANT)

✅ SAFE FIX (RECOMMENDED)
UPDATE devices
SET user_id = '2f7930f0-c583-48a5-81c8-6ce69586ae0c',
    is_active = true
WHERE device_id = '22b6fded-e4fa-40c8-a7e9-e89e814a0bd5';

OR agar device missing ho:

INSERT INTO devices (device_id, user_id, name, is_active)
VALUES (
  '22b6fded-e4fa-40c8-a7e9-e89e814a0bd5',
  '2f7930f0-c583-48a5-81c8-6ce69586ae0c',
  'vikas vender',
  true
);
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import uuid
from datetime import datetime

def fix_device_ownership():
    """Fix device ownership in database"""
    
    # Database connection
    db_url = 'postgresql://whatsapp_patform_user:cCR4XEVKwlV3XdoOmWbGw6rdNTyBOppm@dpg-d5fp9qlactks739q3o20-a.oregon-postgres.render.com/whatsapp_patform?sslmode=require'
    
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Device details
        device_id = '22b6fded-e4fa-40c8-a7e9-e89e814a0bd5'
        user_id = '2f7930f0-c583-48a5-81c8-6ce69586ae0c'  # Current user ID
        device_name = 'vikas vender'
        device_type = 'web'
        
        print(f"🔧 FIXING DEVICE OWNERSHIP")
        print(f"   Device ID: {device_id}")
        print(f"   User ID: {user_id}")
        print(f"   Device Name: {device_name}")
        
        # Check if device exists
        cursor.execute('SELECT device_id FROM devices WHERE device_id = %s', (device_id,))
        existing_device = cursor.fetchone()
        
        if existing_device:
            print("✅ Device exists in DB - Updating ownership...")
            
            # Update existing device
            cursor.execute('''
                UPDATE devices 
                SET busi_user_id = %s,
                    device_name = %s,
                    device_type = %s,
                    session_status = 'connected',
                    updated_at = %s
                WHERE device_id = %s
            ''', (user_id, device_name, device_type, datetime.utcnow(), device_id))
            
            print("✅ Device ownership updated successfully")
            
        else:
            print("❌ Device missing in DB - Creating new device record...")
            
            # Insert new device
            cursor.execute('''
                INSERT INTO devices (
                    device_id, 
                    busi_user_id, 
                    device_name, 
                    device_type, 
                    session_status,
                    created_at, 
                    updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (device_id, user_id, device_name, device_type, 'connected', datetime.utcnow(), datetime.utcnow()))
            
            print("✅ Device created successfully")
        
        # Verify the fix
        cursor.execute('SELECT device_id, busi_user_id, session_status, device_name FROM devices WHERE device_id = %s', (device_id,))
        result = cursor.fetchone()
        
        if result:
            print("\n✅ VERIFICATION - Device after fix:")
            print(f"   device_id: {result['device_id']}")
            print(f"   busi_user_id: {result['busi_user_id']}")
            print(f"   session_status: {result['session_status']}")
            print(f"   device_name: {result['device_name']}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("\n🎉 DEVICE OWNERSHIP FIX COMPLETE!")
        
        return True
        
    except Exception as e:
        print(f'❌ Database error: {e}')
        return False

if __name__ == "__main__":
    fix_device_ownership()
