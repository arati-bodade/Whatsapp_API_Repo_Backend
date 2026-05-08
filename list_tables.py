from db.session import SessionLocal
from sqlalchemy import text

def list_tables_and_counts():
    db = SessionLocal()
    res = db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")).fetchall()
    tables = [r[0] for r in res]
    print(f"Tables in public schema:")
    for t in tables:
        try:
            count = db.execute(text(f"SELECT count(*) FROM {t}")).scalar()
            print(f"TABLE: {t:30} | COUNT: {count}")
        except Exception as e:
            print(f"TABLE: {t:30} | ERROR: {e}")

if __name__ == "__main__":
    list_tables_and_counts()
