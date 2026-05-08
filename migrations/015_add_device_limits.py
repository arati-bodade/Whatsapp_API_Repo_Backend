#!/usr/bin/env python3
"""
Migration script to add device limit fields to businesses table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from db.base import engine

def migrate_device_limits():
    """Add max_devices and allow_unlimited_devices columns to businesses table"""
    
    print("🔄 Starting device limit migration...")
    
    try:
        with engine.connect() as conn:
            # Check if columns already exist
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'businesses' 
                AND column_name IN ('max_devices', 'allow_unlimited_devices')
            """))
            
            existing_columns = [row[0] for row in result.fetchall()]
            print(f"Existing columns: {existing_columns}")
            
            # Add max_devices column if not exists
            if 'max_devices' not in existing_columns:
                print("➕ Adding max_devices column...")
                conn.execute(text("""
                    ALTER TABLE businesses 
                    ADD COLUMN max_devices INTEGER DEFAULT 5
                """))
                print("✅ max_devices column added successfully")
            else:
                print("⏭️ max_devices column already exists")
            
            # Add allow_unlimited_devices column if not exists
            if 'allow_unlimited_devices' not in existing_columns:
                print("➕ Adding allow_unlimited_devices column...")
                conn.execute(text("""
                    ALTER TABLE businesses 
                    ADD COLUMN allow_unlimited_devices BOOLEAN DEFAULT FALSE
                """))
                print("✅ allow_unlimited_devices column added successfully")
            else:
                print("⏭️ allow_unlimited_devices column already exists")
            
            # Update existing records to have default values
            print("🔄 Updating existing records with default values...")
            conn.execute(text("""
                UPDATE businesses 
                SET max_devices = 5 
                WHERE max_devices IS NULL
            """))
            
            conn.execute(text("""
                UPDATE businesses 
                SET allow_unlimited_devices = FALSE 
                WHERE allow_unlimited_devices IS NULL
            """))
            
            conn.commit()
            print("✅ Migration completed successfully!")
            
            # Show summary
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) as total_users,
                    COUNT(CASE WHEN allow_unlimited_devices = TRUE THEN 1 END) as unlimited_users,
                    AVG(max_devices) as avg_max_devices
                FROM businesses
            """))
            
            summary = result.fetchone()
            print(f"\n📊 Migration Summary:")
            print(f"   Total users: {summary[0]}")
            print(f"   Unlimited device users: {summary[1]}")
            print(f"   Average max devices: {summary[2]}")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    migrate_device_limits()
