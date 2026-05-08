from sqlalchemy import text
from db.base import engine

def upgrade():
    with engine.connect() as connection:
        print("Applying migration 013: Adding timestamps to business_user_analytics...")
        
        # Add generated_at column if it doesn't exist
        try:
            connection.execute(text("""
                ALTER TABLE business_user_analytics 
                ADD COLUMN IF NOT EXISTS generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL;
            """))
            print("Added generated_at column.")
        except Exception as e:
            print(f"Error adding generated_at: {e}")

        # Add updated_at column if it doesn't exist
        try:
            connection.execute(text("""
                ALTER TABLE business_user_analytics 
                ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL;
            """))
            print("Added updated_at column.")
        except Exception as e:
            print(f"Error adding updated_at: {e}")

        connection.commit()
        print("Migration 013 complete.")
