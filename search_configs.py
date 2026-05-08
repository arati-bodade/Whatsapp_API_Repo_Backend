from db.session import SessionLocal
from sqlalchemy import text

def search_configs(query):
    db = SessionLocal()
    tables = ["unofficial_whatsapps", "official_whatsapp_configs", "whatsapp_templates"]
    for t in tables:
        try:
            print(f"Searching {t} for '{query}'...")
            rows = db.execute(text(f"SELECT * FROM {t}")).fetchall()
            for row in rows:
                if query.lower() in str(row).lower():
                    print(f"FOUND in {t}: {row}")
        except Exception as e:
            pass

if __name__ == "__main__":
    search_configs("Patil")
    search_configs("Rahul")
