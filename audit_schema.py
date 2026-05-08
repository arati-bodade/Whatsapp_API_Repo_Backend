from db.session import engine
from sqlalchemy import text

def audit_schema():
    print("Auditing PostgreSQL Schema for UUID inconsistencies...")
    with engine.connect() as conn:
        res = conn.execute(text("""
            SELECT table_name, column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND (column_name LIKE '%_id' OR column_name = 'id')
            ORDER BY table_name, column_name;
        """))
        
        mismatches = []
        for row in res.fetchall():
            table, column, dtype = row
            # We expect UUID for most ID columns in our new standard
            if dtype == 'character varying':
                mismatches.append(f"{table}.{column}: {dtype}")
                print(f"POTENTIAL MISMATCH: {table}.{column} is {dtype}")
        
        if not mismatches:
            print("DONE: All checked ID columns are using appropriate types.")
        else:
            print(f"\nRESULT: Found {len(mismatches)} columns using 'character varying' that likely should be 'UUID'.")

if __name__ == "__main__":
    audit_schema()
