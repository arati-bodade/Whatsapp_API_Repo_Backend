from db.base import engine
from sqlalchemy import text

def remove_duplicate_conversations():
    """Remove duplicate conversations, keeping only the latest message per device+phone combination"""
    
    print("🧹 CLEANING DUPLICATE CONVERSATIONS")
    print("=" * 50)
    
    try:
        with engine.connect() as conn:
            # Find duplicates to remove (keep latest, remove older)
            result = conn.execute(text("""
                WITH ranked_messages AS (
                    SELECT 
                        id,
                        device_id,
                        phone_number,
                        incoming_time,
                        ROW_NUMBER() OVER (
                            PARTITION BY device_id, phone_number 
                            ORDER BY incoming_time DESC
                        ) as rn
                    FROM whatsapp_inbox
                    WHERE chat_type = 'individual'
                )
                SELECT id, device_id, phone_number
                FROM ranked_messages
                WHERE rn > 1
            """))
            duplicates_to_remove = result.fetchall()
            
            if len(duplicates_to_remove) == 0:
                print("✅ No duplicates found")
                return True
            
            print(f"📊 Found {len(duplicates_to_remove)} duplicate records to remove")
            
            # Remove duplicates
            duplicate_ids = [str(dup[0]) for dup in duplicates_to_remove]
            
            # Build IN clause for PostgreSQL UUID
            id_list = "', '".join(duplicate_ids)
            
            result = conn.execute(text(f"""
                DELETE FROM whatsapp_inbox 
                WHERE id IN ('{id_list}')
            """))
            
            conn.commit()
            
            print(f"✅ Removed {result.rowcount} duplicate records")
            
            # Verify cleanup
            result = conn.execute(text("""
                SELECT COUNT(*) as total,
                       COUNT(DISTINCT device_id || phone_number) as unique_conversations
                FROM whatsapp_inbox
                WHERE chat_type = 'individual'
            """))
            final_stats = result.fetchone()
            
            print(f"\n📈 Final Statistics:")
            print(f"   Total messages: {final_stats[0]}")
            print(f"   Unique conversations: {final_stats[1]}")
            
            if final_stats[0] == final_stats[1]:
                print("✅ Perfect 1:1 conversation ratio achieved!")
            else:
                print(f"⚠️  Still {final_stats[0] - final_stats[1]} duplicates remaining")
            
            return True
            
    except Exception as e:
        print(f"❌ Error removing duplicates: {e}")
        return False

if __name__ == "__main__":
    remove_duplicate_conversations()
