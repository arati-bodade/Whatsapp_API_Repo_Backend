from db.base import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        # Add chat_type column manually
        conn.execute(text("ALTER TABLE whatsapp_inbox ADD COLUMN chat_type VARCHAR DEFAULT 'individual'"))
        conn.commit()
        print('✅ chat_type column added successfully')
        
        # Verify both columns exist
        result = conn.execute(text("""
            SELECT column_name, data_type, column_default 
            FROM information_schema.columns 
            WHERE table_name = 'whatsapp_inbox' 
            AND column_name IN ('contact_name', 'chat_type')
        """))
        columns = result.fetchall()
        
        print('\n✅ Both columns verified:')
        for col in columns:
            print(f'  - {col[0]}: {col[1]} (default: {col[2]})')
            
        # Update existing records to have chat_type = 'individual'
        result = conn.execute(text("UPDATE whatsapp_inbox SET chat_type = 'individual' WHERE chat_type IS NULL"))
        conn.commit()
        print(f'\n✅ Updated {result.rowcount} existing records with chat_type = individual')
            
except Exception as e:
    print(f'❌ Error: {e}')
