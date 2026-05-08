from db.session import SessionLocal
from sqlalchemy import text

def print_counts():
    db = SessionLocal()
    res = db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")).fetchall()
    for r in res:
        count = db.execute(text(f"SELECT count(*) FROM {r[0]}")).scalar()
        print(f"{r[0]}: {count}")

if __name__ == "__main__":
    print_counts()
