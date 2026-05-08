from db.base import engine
from sqlalchemy import text

def cleanup_old_records():
    """Clean up old records to fix broken data"""
    try:
        with engine.connect() as conn:
            # Fix chat_type for NULL values
            result1 = conn.execute(text("""
                UPDATE whatsapp_inbox 
                SET chat_type = 'individual' 
                WHERE chat_type IS NULL
            """))
            
            # Fix contact_name for NULL values
            result2 = conn.execute(text("""
                UPDATE whatsapp_inbox 
                SET contact_name = phone_number 
                WHERE contact_name IS NULL
            """))
            
            conn.commit()
            
            print(f"✅ Fixed {result1.rowcount} records with NULL chat_type")
            print(f"✅ Fixed {result2.rowcount} records with NULL contact_name")
            
            # Verify results
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN chat_type = 'individual' THEN 1 END) as individual_chats,
                    COUNT(CASE WHEN contact_name IS NOT NULL THEN 1 END) as with_contact_name,
                    COUNT(CASE WHEN contact_name IS NULL THEN 1 END) as missing_contact_name
                FROM whatsapp_inbox
            """))
            
            stats = result.fetchone()
            print(f"\n📊 Database Statistics:")
            print(f"  Total messages: {stats[0]}")
            print(f"  Individual chats: {stats[1]}")
            print(f"  With contact name: {stats[2]}")
            print(f"  Missing contact name: {stats[3]}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error cleaning up records: {e}")
        return False

if __name__ == "__main__":
    cleanup_old_records()
