from sqlalchemy import text
from db.session import SessionLocal

def cleanup_db():
    db = SessionLocal()
    try:
        print("Starting Database Cleanup...")
        
        # SQL to delete invalid entries
        sql = text("""
        DELETE FROM whatsapp_inbox 
        WHERE phone_number LIKE '%@%'
           OR LENGTH(phone_number) > 15
           OR phone_number LIKE '385%'  -- Remove the specific bad number range
           OR phone_number = '188768292233321';
        """)
        
        result = db.execute(sql)
        db.commit()
        print(f"Cleanup complete. Deleted {result.rowcount} invalid rows.")
        
    except Exception as e:
        print(f"Error during cleanup: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_db()
