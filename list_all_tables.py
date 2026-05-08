from db.session import SessionLocal
from sqlalchemy import text

def list_all_schemas_and_tables():
    db = SessionLocal()
    schemas = db.execute(text("SELECT schema_name FROM information_schema.schemata")).fetchall()
    print(f"Schemas: {[s[0] for s in schemas]}")
    for s in schemas:
        s_name = s[0]
        if s_name.startswith("pg_") or s_name == "information_schema":
            continue
        print(f"\nSCHEMA: {s_name}")
        tables = db.execute(text(f"SELECT table_name FROM information_schema.tables WHERE table_schema = '{s_name}'")).fetchall()
        for t in tables:
            try:
                count = db.execute(text(f"SELECT count(*) FROM {s_name}.{t[0]}")).scalar()
                print(f"  Table: {t[0]:30} | Count: {count}")
            except:
                print(f"  Table: {t[0]:30} | (Error counting)")

if __name__ == "__main__":
    list_all_schemas_and_tables()
