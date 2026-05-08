#!/usr/bin/env python3

from sqlalchemy import inspect, text
from db.base import engine

def check_devices_table():
    """Check the devices table structure"""
    
    try:
        # Create inspector
        inspector = inspect(engine)
        
        # Check devices table
        if 'devices' in inspector.get_table_names():
            print("✅ 'devices' table exists")
            
            # Get table structure
            columns = inspector.get_columns('devices')
            print("\nColumns in 'devices' table:")
            for column in columns:
                print(f"  - {column['name']}: {column['type']}")
                
            # Check busi_user_id column specifically
            busi_user_id_col = next((col for col in columns if col['name'] == 'busi_user_id'), None)
            if busi_user_id_col:
                print(f"\n🔍 busi_user_id column type: {busi_user_id_col['type']}")
                print(f"   Is UUID type: {'UUID' in str(busi_user_id_col['type'])}")
        else:
            print("❌ 'devices' table does not exist")
            
    except Exception as e:
        print(f"❌ Error checking devices table: {e}")

if __name__ == "__main__":
    check_devices_table()
