from db.session import SessionLocal
from sqlalchemy import text
import json

def dump_configs():
    db = SessionLocal()
    tables = ["unofficial_whatsapps", "official_whatsapp_configs"]
    results = {}
    for t in tables:
        try:
            columns_res = db.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{t}'")).fetchall()
            cols = [c[0] for c in columns_res]
            rows = db.execute(text(f"SELECT * FROM {t}")).fetchall()
            
            data = []
            for row in rows:
                data.append(dict(zip(cols, row)))
            results[t] = data
        except Exception as e:
            results[t] = str(e)

    with open("configs_dump.json", "w") as f:
        json.dump(results, f, indent=4, default=str)
    print("Configs dumped to configs_dump.json")

if __name__ == "__main__":
    dump_configs()
