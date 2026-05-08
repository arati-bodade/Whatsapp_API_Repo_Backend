from sqlalchemy import create_engine, text
import os

# Database URL
DATABASE_URL = "postgresql://whatsapp_patform_user:cCR4XEVKwlV3XdoOmWbGw6rdNTyBOppm@dpg-d5fp9qlactks739q3o20-a.oregon-postgres.render.com/whatsapp_patform?sslmode=require"

def inspect_db():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print("--- Inspecting sheetstatus Enum ---")
        try:
            result = conn.execute(text("SELECT unnest(enum_range(NULL::sheetstatus))"))
            rows = result.fetchall()
            with open("enum_output.txt", "w") as f:
                f.write(str(rows))
            print("Wrote to enum_output.txt")
        except Exception as e:
            print(f"Error inspecting enum: {e}")

        print("\n--- Inspecting google_sheets.status column ---")
        try:
            result = conn.execute(text("SELECT column_name, data_type, udt_name FROM information_schema.columns WHERE table_name = 'google_sheets' AND column_name = 'status'"))
            row = result.fetchone()
            print(f"Column info: {row}")
        except Exception as e:
            print(f"Error inspecting column: {e}")

if __name__ == "__main__":
    inspect_db()
