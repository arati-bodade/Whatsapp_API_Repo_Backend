"""
Add Message Model Migration

Creates messages table for WhatsApp message tracking.
Includes enums for message types, status, and modes.
"""

from sqlalchemy import create_engine, text
from core.config import settings


def upgrade():
    """Create messages table and enums."""
    engine = create_engine(settings.DATABASE_URL)
    
    # Create enum types first (each in separate transaction)
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE TYPE channeltype AS ENUM ('WHATSAPP');"))
            conn.commit()
    except Exception:
        pass  # Type already exists
    
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE TYPE messagemode AS ENUM ('OFFICIAL', 'UNOFFICIAL');"))
            conn.commit()
    except Exception:
        pass  # Type already exists
    
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE TYPE messagetype AS ENUM ('OTP', 'TEXT', 'TEMPLATE', 'MEDIA');"))
            conn.commit()
    except Exception:
        pass  # Type already exists
    
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE TYPE messagestatus AS ENUM ('PENDING', 'SENT', 'DELIVERED', 'READ', 'FAILED');"))
            conn.commit()
    except Exception:
        pass  # Type already exists
    
    # Now create the messages table in a separate transaction
    with engine.connect() as connection:
        # Create messages table
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS messages (
                message_id VARCHAR(50) PRIMARY KEY,
                user_id VARCHAR(100) NOT NULL,
                channel channeltype NOT NULL DEFAULT 'WHATSAPP',
                mode messagemode NOT NULL,
                sender_number VARCHAR(20) NOT NULL,
                receiver_number VARCHAR(20) NOT NULL,
                message_type messagetype NOT NULL,
                template_name VARCHAR(100),
                message_body TEXT NOT NULL,
                status messagestatus NOT NULL DEFAULT 'PENDING',
                credits_used INTEGER NOT NULL DEFAULT 1,
                sent_at TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE
            );
        """))
        
        # Create indexes for better performance
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_messages_user_id ON messages(user_id);"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_messages_status ON messages(status);"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_messages_message_type ON messages(message_type);"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_messages_receiver_number ON messages(receiver_number);"))
        
        connection.commit()
        print("✅ Messages table created successfully")


def downgrade():
    """Remove messages table and enums (rollback)."""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as connection:
        # Drop indexes first
        connection.execute(text("DROP INDEX IF EXISTS idx_messages_user_id;"))
        connection.execute(text("DROP INDEX IF EXISTS idx_messages_status;"))
        connection.execute(text("DROP INDEX IF EXISTS idx_messages_message_type;"))
        connection.execute(text("DROP INDEX IF EXISTS idx_messages_created_at;"))
        connection.execute(text("DROP INDEX IF EXISTS idx_messages_receiver_number;"))
        
        # Drop table
        connection.execute(text("DROP TABLE IF EXISTS messages;"))
        
        # Drop enums
        connection.execute(text("DROP TYPE IF EXISTS channeltype;"))
        connection.execute(text("DROP TYPE IF EXISTS messagemode;"))
        connection.execute(text("DROP TYPE IF EXISTS messagetype;"))
        connection.execute(text("DROP TYPE IF EXISTS messagestatus;"))
        
        connection.commit()
        print("⚠️ Messages table and enums dropped (rollback)")
