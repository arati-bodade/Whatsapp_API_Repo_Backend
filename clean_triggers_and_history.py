import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv('DATABASE_URL')
engine = create_engine(db_url)

with engine.connect() as conn:
    print("🧹 CLEANING TRIGGERS AND TRIGGER HISTORY")
    print("=" * 50)
    
    # Check and clean current triggers
    print("\n1. Checking current triggers...")
    result = conn.execute(text('SELECT COUNT(*) FROM google_sheet_triggers'))
    trigger_count = result.scalar()
    print(f'   Current triggers count: {trigger_count}')
    
    if trigger_count > 0:
        result = conn.execute(text('DELETE FROM google_sheet_triggers'))
        print(f'   ✅ Deleted {result.rowcount} triggers')
        conn.commit()
        
        result = conn.execute(text('SELECT COUNT(*) FROM google_sheet_triggers'))
        final_count = result.scalar()
        print(f'   Final triggers count: {final_count}')
    else:
        print('   No triggers to delete')
    
    # Check and clean trigger history
    print("\n2. Checking trigger history...")
    result = conn.execute(text('SELECT COUNT(*) FROM sheet_trigger_history'))
    history_count = result.scalar()
    print(f'   Current trigger history count: {history_count}')
    
    if history_count > 0:
        result = conn.execute(text('DELETE FROM sheet_trigger_history'))
        print(f'   ✅ Deleted {result.rowcount} trigger history records')
        conn.commit()
        
        result = conn.execute(text('SELECT COUNT(*) FROM sheet_trigger_history'))
        final_history_count = result.scalar()
        print(f'   Final trigger history count: {final_history_count}')
    else:
        print('   No trigger history to delete')
    
    print("\n" + "=" * 50)
    print("✅ TRIGGERS AND HISTORY CLEANUP COMPLETE")
