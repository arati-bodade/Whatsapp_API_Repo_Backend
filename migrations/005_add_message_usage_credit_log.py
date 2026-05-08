"""
Message Usage Credit Log Migration

Creates the message_usage_credit_logs table to track
credit usage for WhatsApp messages.
"""

from sqlalchemy import create_engine, text
from core.config import settings


def upgrade():
    """Create message_usage_credit_logs table."""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as connection:
        # Create message_usage_credit_logs table
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS message_usage_credit_logs (
                usage_id VARCHAR(50) PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL,
                message_id VARCHAR(255) NOT NULL,
                credits_deducted INTEGER NOT NULL CHECK (credits_deducted > 0),
                balance_after INTEGER NOT NULL CHECK (balance_after >= 0),
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """))
        
        # Create indexes for better performance
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_message_usage_user_id ON message_usage_credit_logs(user_id);"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_message_usage_message_id ON message_usage_credit_logs(message_id);"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_message_usage_timestamp ON message_usage_credit_logs(timestamp);"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_message_usage_user_timestamp ON message_usage_credit_logs(user_id, timestamp);"))
        
        connection.commit()
        print("✅ Message usage credit logs table created successfully")


def downgrade():
    """Remove the message_usage_credit_logs table (rollback)."""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as connection:
        connection.execute(text("DROP TABLE IF EXISTS message_usage_credit_logs;"))
        connection.commit()
        print("⚠️ Message usage credit logs table dropped (rollback)")
