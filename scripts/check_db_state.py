import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, inspect, text
from core.config import settings

def check_db():
    print("Connecting...")
    engine = create_engine(settings.DATABASE_URL)
    inspector = inspect(engine)
    
    try:
        columns = [c['name'] for c in inspector.get_columns('google_sheets')]
        print(f"Columns in google_sheets: {columns}")
        
        # Test query
        with engine.connect() as conn:
            try:
                conn.execute(text("SELECT id FROM google_sheets LIMIT 1"))
                print("SELECT id FROM google_sheets -> SUCCESS")
            except Exception as e:
                print(f"SELECT id FROM google_sheets -> FAILED: {e}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_db()
