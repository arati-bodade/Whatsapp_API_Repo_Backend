from db.session import SessionLocal
from sqlalchemy import text
import json

def search_for_patil():
    db = SessionLocal()
    res = db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")).fetchall()
    tables = [r[0] for r in res]
    
    hits = []
    for t in tables:
        try:
            rows = db.execute(text(f"SELECT * FROM {t}")).fetchall()
            for row in rows:
                if "patil" in str(row).lower():
                    # Get column names
                    cols_res = db.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{t}'")).fetchall()
                    cols = [c[0] for c in cols_res]
                    hits.append({"table": t, "row": dict(zip(cols, row))})
        except:
            pass
            
    with open("patil_search.json", "w") as f:
        json.dump(hits, f, indent=4, default=str)
    print(f"Done. Found {len(hits)} hits.")

if __name__ == "__main__":
    search_for_patil()
