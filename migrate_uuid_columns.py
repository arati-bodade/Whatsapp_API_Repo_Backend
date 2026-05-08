#!/usr/bin/env python3

import sys
sys.path.append('.')

from db.base import engine
from sqlalchemy import text
import uuid

def migrate_uuid_columns():
    """Migrate string columns to UUID columns in the database"""
    
    print("🔄 Starting UUID column migration...")
    
    with engine.connect() as conn:
        # Begin transaction
        trans = conn.begin()
        
        try:
            # 1. Check current schema
            print("\n📊 Checking current schema...")
            
            # Check businesses table
            result = conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'businesses' 
                AND column_name IN ('busi_user_id', 'parent_reseller_id')
            """))
            businesses_schema = result.fetchall()
            print(f"   Businesses schema: {businesses_schema}")
            
            # Check devices table
            result = conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'devices' 
                AND column_name IN ('device_id', 'busi_user_id')
            """))
            devices_schema = result.fetchall()
            print(f"   Devices schema: {devices_schema}")
            
            # Check messages table
            result = conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'messages' 
                AND column_name IN ('message_id', 'busi_user_id')
            """))
            messages_schema = result.fetchall()
            print(f"   Messages schema: {messages_schema}")
            
            # 2. Migrate businesses table
            print("\n🔄 Migrating businesses table...")
            
            # Convert busi_user_id from varchar to uuid
            conn.execute(text("""
                ALTER TABLE businesses 
                ALTER COLUMN busi_user_id TYPE UUID USING busi_user_id::UUID
            """))
            
            # Convert parent_reseller_id from varchar to uuid (if needed)
            try:
                conn.execute(text("""
                    ALTER TABLE businesses 
                    ALTER COLUMN parent_reseller_id TYPE UUID USING parent_reseller_id::UUID
                """))
                print("   ✅ parent_reseller_id migrated to UUID")
            except Exception as e:
                print(f"   ⚠️ parent_reseller_id migration skipped: {e}")
            
            # 3. Migrate devices table
            print("\n🔄 Migrating devices table...")
            
            # Convert device_id from varchar to uuid
            conn.execute(text("""
                ALTER TABLE devices 
                ALTER COLUMN device_id TYPE UUID USING device_id::UUID
            """))
            
            # Convert busi_user_id from varchar to uuid
            conn.execute(text("""
                ALTER TABLE devices 
                ALTER COLUMN busi_user_id TYPE UUID USING busi_user_id::UUID
            """))
            
            # 4. Migrate messages table
            print("\n🔄 Migrating messages table...")
            
            # Convert message_id from varchar to uuid
            conn.execute(text("""
                ALTER TABLE messages 
                ALTER COLUMN message_id TYPE UUID USING message_id::UUID
            """))
            
            # Convert busi_user_id from varchar to uuid (if needed)
            try:
                conn.execute(text("""
                    ALTER TABLE messages 
                    ALTER COLUMN busi_user_id TYPE UUID USING busi_user_id::UUID
                """))
                print("   ✅ messages.busi_user_id migrated to UUID")
            except Exception as e:
                print(f"   ⚠️ messages.busi_user_id migration skipped: {e}")
            
            # 5. Verify migration
            print("\n✅ Verifying migration...")
            
            result = conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'businesses' 
                AND column_name IN ('busi_user_id', 'parent_reseller_id')
            """))
            print(f"   Businesses after: {result.fetchall()}")
            
            result = conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'devices' 
                AND column_name IN ('device_id', 'busi_user_id')
            """))
            print(f"   Devices after: {result.fetchall()}")
            
            result = conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'messages' 
                AND column_name IN ('message_id', 'busi_user_id')
            """))
            print(f"   Messages after: {result.fetchall()}")
            
            # Commit transaction
            trans.commit()
            
            print("\n🎉 UUID migration completed successfully!")
            return True
            
        except Exception as e:
            # Rollback on error
            trans.rollback()
            print(f"\n❌ Migration failed: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = migrate_uuid_columns()
    sys.exit(0 if success else 1)
