"""
Add Campaign Models

Revision ID: 021_add_campaign_models
Revises: 020_replace_device_unique_constraint
Create Date: 2026-03-01 19:00:00.000000

"""
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from db.base import engine

def upgrade():
    print("🔄 Adding campaign models...")
    try:
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            # 1. campaigns table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS campaigns (
                    id UUID PRIMARY KEY,
                    busi_user_id UUID NOT NULL REFERENCES businesses(busi_user_id) ON DELETE CASCADE,
                    sheet_id UUID NOT NULL REFERENCES google_sheets(id) ON DELETE CASCADE,
                    name VARCHAR(255),
                    status VARCHAR(50) DEFAULT 'Pending',
                    session_number INTEGER DEFAULT 1,
                    total_recipients INTEGER DEFAULT 0,
                    sent_count INTEGER DEFAULT 0,
                    failed_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """))

            # 2. campaign_devices table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS campaign_devices (
                    id UUID PRIMARY KEY,
                    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
                    device_id UUID NOT NULL REFERENCES devices(device_id) ON DELETE CASCADE
                );
            """))

            # 3. message_templates table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS message_templates (
                    id UUID PRIMARY KEY,
                    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
                    content TEXT NOT NULL,
                    delay_override INTEGER
                );
            """))

            # 4. message_logs table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS message_logs (
                    id UUID PRIMARY KEY,
                    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
                    device_id UUID REFERENCES devices(device_id) ON DELETE SET NULL,
                    recipient VARCHAR(50) NOT NULL,
                    template_id UUID REFERENCES message_templates(id) ON DELETE SET NULL,
                    status VARCHAR(50) NOT NULL,
                    retry_count INTEGER DEFAULT 0,
                    response_time INTEGER,
                    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """))
            print("✅ Campaign models added successfully!")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise

def downgrade():
    print("🔄 Reverting campaign models...")
    try:
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            conn.execute(text("DROP TABLE IF EXISTS message_logs CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS message_templates CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS campaign_devices CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS campaigns CASCADE;"))
            print("✅ Reverted campaign models successfully!")
    except Exception as e:
        print(f"❌ Downgrade failed: {e}")
        raise

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        downgrade()
    else:
        upgrade()
