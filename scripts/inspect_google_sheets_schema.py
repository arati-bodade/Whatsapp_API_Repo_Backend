import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import inspect, text
from db.base import engine

def inspect_schema():
    try:
        inspector = inspect(engine)
        
        for table_name in ["google_sheets", "sheet_trigger_history"]:
            print(f"\n--- Table: {table_name} ---")
            if table_name not in inspector.get_table_names():
                print(f"ERROR: Table '{table_name}' does not exist!")
                continue

            columns = inspector.get_columns(table_name)
            print(f"Columns:")
            for col in columns:
                print(f"- {col['name']} ({col['type']})")
                
            pk_constraint = inspector.get_pk_constraint(table_name)
            print(f"Primary Key: {pk_constraint}")
            
            fks = inspector.get_foreign_keys(table_name)
            print(f"Foreign Keys: {fks}")

    except Exception as e:
        print(f"Error inspecting schema: {e}")

if __name__ == "__main__":
    inspect_schema()
