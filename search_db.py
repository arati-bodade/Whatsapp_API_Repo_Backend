from db.session import SessionLocal
from sqlalchemy import text

def search_db(query):
    db = SessionLocal()
    res = db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")).fetchall()
    tables = [r[0] for r in res]
    print(f"Searching {len(tables)} tables for '{query}'...")
    for t in tables:
        try:
            # Get columns to avoid issues with non-text searches if needed, 
            # but simplest is to cast the entire row to string for a rough search
            rows = db.execute(text(f"SELECT * FROM {t}")).fetchall()
            for row in rows:
                if query.lower() in str(row).lower():
                    print(f"FOUND in {t}: {row}")
        except Exception as e:
            # print(f"Error searching {t}: {e}")
            pass

if __name__ == "__main__":
    search_db("Patil")
    search_db("Rahul")
