from sqlalchemy import create_engine, inspect, text
import os
from dotenv import load_dotenv

load_dotenv()

def get_schema():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not found in .env")
        return
        
    engine = create_engine(db_url)
    inspector = inspect(engine)
    
    tables = inspector.get_table_names()
    print(f"Tables: {tables}")
    
    for table in ['devices', 'google_sheet_triggers', 'google_sheets', 'sheet_trigger_history']:
        if table in tables:
            columns = [c['name'] for c in inspector.get_columns(table)]
            print(f"\nTable '{table}' columns: {columns}")
            
            with engine.connect() as conn:
                count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                print(f"Row count: {count}")

if __name__ == "__main__":
    get_schema()
