"""
Add media columns to campaigns

Revision ID: 022_add_campaign_media_columns
Revises: 021_add_campaign_models
Create Date: 2026-03-02 01:40:00.000000

"""
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from db.base import engine

def upgrade():
    print("🔄 Adding media columns to campaigns table...")
    try:
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            # Add columns if they don't exist
            conn.execute(text("""
                ALTER TABLE campaigns 
                ADD COLUMN IF NOT EXISTS media_url TEXT,
                ADD COLUMN IF NOT EXISTS media_type VARCHAR(50);
            """))
            print("✅ Media columns added successfully!")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        # raise # Don't raise so it doesn't break if already exists

def downgrade():
    print("🔄 Removing media columns from campaigns table...")
    try:
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            conn.execute(text("""
                ALTER TABLE campaigns 
                DROP COLUMN IF EXISTS media_url,
                DROP COLUMN IF EXISTS media_type;
            """))
            print("✅ Media columns removed successfully!")
    except Exception as e:
        print(f"❌ Downgrade failed: {e}")
        raise

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        downgrade()
    else:
        upgrade()
