#!/.        usr/bin/env python3

from sqlalchemy import inspect, text
from db.base import engine

def check_businesses_table():
    """Check the structure of the businesses table"""
    
    try:
        # Create inspector
        inspector = inspect(engine)
        
        # Check if businesses table exists
        if 'businesses' not in inspector.get_table_names():
            print("❌ 'businesses' table does not exist!")
            return
            
        print("✅ 'businesses' table exists")
        
        # Get table structure
        columns = inspector.get_columns('businesses')
        
        print("\nColumns in 'businesses' table:")
        for column in columns:
            print(f"  - {column['name']}: {column['type']}")
            
        # Check primary key
        pk_columns = inspector.get_pk_constraint('businesses')
        print(f"\nPrimary Key: {pk_columns['constrained_columns']}")
        
        # Check foreign keys
        fks = inspector.get_foreign_keys('businesses')
        print(f"\nForeign Keys: {len(fks)} found")
        for fk in fks:
            print(f"  - {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")
            
    except Exception as e:
        print(f"❌ Error checking businesses table: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_businesses_table()
