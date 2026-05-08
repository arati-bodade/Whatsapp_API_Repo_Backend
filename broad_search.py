from db.session import SessionLocal
from sqlalchemy import text

def broad_search(db, query):
    res = db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")).fetchall()
    tables = [r[0] for r in res]
    for t in tables:
        try:
            rows = db.execute(text(f"SELECT * FROM {t}")).fetchall()
            for row in rows:
                if query.lower() in str(row).lower():
                    print(f"FOUND in {t}: {row}")
        except:
            pass

if __name__ == "__main__":
    db = SessionLocal()
    print("Broad searching...")
    broad_search(db, "Rah")
    broad_search(db, "Pat")
