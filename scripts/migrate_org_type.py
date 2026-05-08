from sqlalchemy import text
from db.base import engine

def migrate():
    with engine.connect() as conn:
        print("Starting migration: Adding organization_type to resellers table...")
        try:
            # Check if column exists
            result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='resellers' AND column_name='organization_type'"))
            if not result.fetchone():
                print("Column 'organization_type' does not exist. Adding...")
                conn.execute(text("ALTER TABLE resellers ADD COLUMN organization_type VARCHAR(100)"))
                conn.commit()
                print("Successfully added 'organization_type' column.")
            else:
                print("Column 'organization_type' already exists.")
        except Exception as e:
            print(f"Error during migration: {e}")

if __name__ == "__main__":
    migrate()
