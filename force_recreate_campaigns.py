import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from db.base import engine

def force_recreate():
    print("🔄 Forcing recreate of campaign tables...")
    try:
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            conn.execute(text("DROP TABLE IF EXISTS message_logs CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS message_templates CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS campaign_devices CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS campaigns CASCADE;"))
            
            # Recreate using the migration script logic
            conn.execute(text("""
                CREATE TABLE campaigns (
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

            conn.execute(text("""
                CREATE TABLE campaign_devices (
                    id UUID PRIMARY KEY,
                    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
                    device_id UUID NOT NULL REFERENCES devices(device_id) ON DELETE CASCADE
                );
            """))

            conn.execute(text("""
                CREATE TABLE message_templates (
                    id UUID PRIMARY KEY,
                    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
                    content TEXT NOT NULL,
                    delay_override INTEGER
                );
            """))

            conn.execute(text("""
                CREATE TABLE message_logs (
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
            print("✅ Campaign models recreated successfully!")
            
    except Exception as e:
        print(f"❌ Recreate failed: {e}")

if __name__ == "__main__":
    force_recreate()
