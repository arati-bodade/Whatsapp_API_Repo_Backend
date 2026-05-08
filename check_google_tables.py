from db.session import SessionLocal
from sqlalchemy import text

def list_google_tables():
    db = SessionLocal()
    try:
        # Check for Google Sheets tables
        print("--- Google Sheets Related Tables ---")
        result = db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")).fetchall()
        for row in result:
            table_name = row[0]
            if 'google' in table_name or 'sheet' in table_name:
                try:
                    count = db.execute(text(f"SELECT count(*) FROM {table_name}")).scalar()
                    print(f"Table: {table_name:30} | Rows: {count}")
                    
                    # If it's the triggers table, show structure
                    if 'trigger' in table_name and 'history' not in table_name:
                        print(f"Columns for {table_name}:")
                        cols = db.execute(text(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table_name}'")).fetchall()
                        for col in cols:
                            print(f"  - {col[0]} ({col[1]})")
                except Exception as e:
                    print(f"Table: {table_name:30} | Error: {e}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    list_google_tables()
