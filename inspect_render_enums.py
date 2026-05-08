import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def inspect_enums():
    db_url = os.getenv("DATABASE_URL")
    if "?sslmode=require" not in db_url:
        db_url += "?sslmode=require"
    
    engine = create_engine(db_url)
    try:
        with engine.connect() as connection:
            print("Inspecting Custom Enum Types in Render DB...")
            
            # Query to get all enum types and their values
            query = """
            SELECT t.typname as enum_name, e.enumlabel as enum_value
            FROM pg_type t 
            JOIN pg_enum e ON t.oid = e.enumtypid  
            JOIN pg_catalog.pg_namespace n ON n.oid = t.typnamespace
            WHERE n.nspname = 'public'
            ORDER BY enum_name, e.enumsortorder;
            """
            
            result = connection.execute(text(query))
            enums = {}
            for row in result:
                name, val = row
                if name not in enums:
                    enums[name] = []
                enums[name].append(val)
                
            for name, values in enums.items():
                print(f"Enum {name}: {values}")
                
            if not enums:
                print("No custom enums found (may be using VARCHAR based 'pseudo-enums')")

    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    inspect_enums()
