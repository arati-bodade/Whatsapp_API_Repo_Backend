#!/usr/bin/env python3
"""
🔥 STEP 1: CHECK DEVICE IN DATABASE
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import os

def check_device_in_database():
    """Check device ownership in database"""
    
    # Database connection
    db_url = 'postgresql://whatsapp_patform_user:cCR4XEVKwlV3XdoOmWbGw6rdNTyBOppm@dpg-d5fp9qlactks739q3o20-a.oregon-postgres.render.com/whatsapp_patform?sslmode=require'
    
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check specific device
        device_id = '22b6fded-e4fa-40c8-a7e9-e89e814a0bd5'
        cursor.execute('SELECT device_id, busi_user_id, session_status, device_name FROM devices WHERE device_id = %s', (device_id,))
        
        result = cursor.fetchone()
        
        if result:
            print('✅ Device found in DB:')
            print(f'   device_id: {result["device_id"]}')
            print(f'   busi_user_id: {result["busi_user_id"]}')
            print(f'   session_status: {result["session_status"]}')
            print(f'   device_name: {result["device_name"]}')
        else:
            print('❌ Device NOT found in DB - This is the problem!')
        
        # Check all devices
        cursor.execute('SELECT device_id, busi_user_id, session_status, device_name FROM devices ORDER BY created_at DESC')
        all_devices = cursor.fetchall()
        
        print(f'\n📋 All devices in DB ({len(all_devices)} total):')
        for device in all_devices:
            print(f'   {device["device_id"]} → user: {device["busi_user_id"]} ({device["session_status"]})')
        
        cursor.close()
        conn.close()
        
        return result
        
    except Exception as e:
        print(f'❌ Database error: {e}')
        return None

if __name__ == "__main__":
    check_device_in_database()
