from db.session import SessionLocal
from sqlalchemy import text

def find_unique_user_ids():
    db = SessionLocal()
    tables = ["unofficial_whatsapps", "official_whatsapp_configs", "whatsapp_templates"]
    all_ids = set()
    for t in tables:
        try:
            print(f"Checking {t}...")
            # Try busi_user_id or user_id
            rows = db.execute(text(f"SELECT * FROM {t} LIMIT 1")).fetchall()
            if not rows:
                print(f"No rows in {t}")
                continue
            
            # Check column names
            # In PostgreSQL, we can check information_schema.columns
            columns_res = db.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{t}'")).fetchall()
            cols = [c[0] for c in columns_res]
            print(f"Columns in {t}: {cols}")
            
            id_col = None
            if "busi_user_id" in cols: id_col = "busi_user_id"
            elif "user_id" in cols: id_col = "user_id"
            
            if id_col:
                distinct_ids = db.execute(text(f"SELECT DISTINCT {id_col} FROM {t}")).fetchall()
                print(f"Unique IDs in {t}: {[r[0] for r in distinct_ids]}")
                for r in distinct_ids: all_ids.add(str(r[0]))
            else:
                print(f"No user ID column found in {t}")
        except Exception as e:
            print(f"Error checking {t}: {e}")
            
    print(f"\nTOTAL UNIQUE USER IDs FOUND: {len(all_ids)}")
    print(all_ids)

if __name__ == "__main__":
    find_unique_user_ids()
