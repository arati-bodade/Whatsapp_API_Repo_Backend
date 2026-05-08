import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import inspect
from db.base import engine

def inspect_exact_types():
    try:
        inspector = inspect(engine)
        
        for table_name in ["google_sheets", "businesses"]:
            print(f"\n--- Table: {table_name} ---")
            columns = inspector.get_columns(table_name)
            for col in columns:
                if col['name'] in ['id', 'user_id', 'busi_user_id']:
                    print(f"- {col['name']}: {col['type']}")
                    
            fks = inspector.get_foreign_keys(table_name)
            for fk in fks:
                print(f"FK: {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")

    except Exception as e:
        print(f"Error inspecting schema: {e}")

if __name__ == "__main__":
    inspect_exact_types()
