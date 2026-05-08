from db.session import SessionLocal
from sqlalchemy import text
import json

def print_counts():
    db = SessionLocal()
    res = db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")).fetchall()
    counts = {}
    for r in res:
        try:
            count = db.execute(text(f"SELECT count(*) FROM {r[0]}")).scalar()
            counts[r[0]] = count
        except:
            counts[r[0]] = "error"
    with open("counts.json", "w") as f:
        json.dump(counts, f, indent=4)
    print("Counts written to counts.json")

if __name__ == "__main__":
    print_counts()
