from sqlalchemy import text
from db.session import get_db

def fix_status_column_length():
    db = next(get_db())
    try:
        print("Checking message_logs table schema...")
        
        # Alter the column length to 255
        sql = text("ALTER TABLE message_logs ALTER COLUMN status TYPE VARCHAR(255)")
        db.execute(sql)
        db.commit()
        
        print("✅ Successfully increased status column length to 255 in message_logs table.")
        
    except Exception as e:
        print(f"❌ Error fixing column length: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_status_column_length()
