from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = "postgresql://whatsapp_patform_user:cCR4XEVKwlV3XdoOmWbGw6rdNTyBOppm@dpg-d5fp9qlactks739q3o20-a.oregon-postgres.render.com/whatsapp_patform"

def fix_schema():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print("Altering sender_number column size...")
        conn.execute(text("ALTER TABLE messages ALTER COLUMN sender_number TYPE VARCHAR(100);"))
        print("Altering receiver_number column size...")
        conn.execute(text("ALTER TABLE messages ALTER COLUMN receiver_number TYPE VARCHAR(50);"))
        conn.commit()
        print("Schema update successful!")

if __name__ == "__main__":
    try:
        fix_schema()
    except Exception as e:
        print(f"Error updating schema: {e}")
