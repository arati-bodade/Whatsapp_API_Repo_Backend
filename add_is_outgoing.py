"""
Migration script: adds is_outgoing column to whatsapp_inbox table.
Run once with: python add_is_outgoing.py
"""
from db.session import engine
from sqlalchemy import text, inspect

def main():
    inspector = inspect(engine)
    cols = [c['name'] for c in inspector.get_columns('whatsapp_inbox')]
    print(f"Current columns: {cols}")

    if 'is_outgoing' not in cols:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE whatsapp_inbox ADD COLUMN is_outgoing BOOLEAN DEFAULT FALSE NOT NULL"))
        print("✅ Added is_outgoing column successfully.")
    else:
        print("ℹ️  is_outgoing column already exists, skipping.")

if __name__ == "__main__":
    main()
