from db.session import SessionLocal
from sqlalchemy import text
import json

def search_for_rahul():
    db = SessionLocal()
    res = db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")).fetchall()
    tables = [r[0] for r in res]
    
    hits = []
    for t in tables:
        try:
            rows = db.execute(text(f"SELECT * FROM {t}")).fetchall()
            for row in rows:
                if "rahul" in str(row).lower():
                    hits.append({"table": t, "row": str(row)})
        except:
            pass
            
    with open("rahul_search.json", "w") as f:
        json.dump(hits, f, indent=4)
    print(f"Done. Found {len(hits)} hits.")

if __name__ == "__main__":
    search_for_rahul()
