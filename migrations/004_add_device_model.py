"""
Add Device Model Migration

Creates devices table for WhatsApp Web device management.
Includes enums for device types and session status.
"""

from sqlalchemy import create_engine, text
from core.config import settings


def upgrade():
    """Create devices table and enums."""
    engine = create_engine(settings.DATABASE_URL)
    
    # Create enum types first (each in separate transaction)
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE TYPE devicetype AS ENUM ('web', 'mobile', 'desktop');"))
            conn.commit()
    except Exception:
        pass  # Type already exists
    
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE TYPE sessionstatus AS ENUM ('connected', 'disconnected', 'pending', 'expired', 'qr_generated');"))
            conn.commit()
    except Exception:
        pass  # Type already exists
    
    # Now create the devices table in a separate transaction
    with engine.connect() as connection:
        # Create devices table
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS devices (
                device_id VARCHAR(50) PRIMARY KEY,
                user_id VARCHAR(100) NOT NULL,
                device_name VARCHAR(255) NOT NULL,
                device_type devicetype NOT NULL,
                session_status sessionstatus NOT NULL DEFAULT 'pending',
                qr_last_generated TIMESTAMP WITH TIME ZONE,
                ip_address VARCHAR(45),
                last_active TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE
            );
        """))
        
        # Create indexes for better performance
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_devices_user_id ON devices(user_id);"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_devices_session_status ON devices(session_status);"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_devices_device_type ON devices(device_type);"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_devices_last_active ON devices(last_active);"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_devices_created_at ON devices(created_at);"))
        
        connection.commit()
        print("✅ Devices table created successfully")


def downgrade():
    """Remove devices table and enums (rollback)."""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as connection:
        # Drop indexes first
        connection.execute(text("DROP INDEX IF EXISTS idx_devices_user_id;"))
        connection.execute(text("DROP INDEX IF EXISTS idx_devices_session_status;"))
        connection.execute(text("DROP INDEX IF EXISTS idx_devices_device_type;"))
        connection.execute(text("DROP INDEX IF EXISTS idx_devices_last_active;"))
        connection.execute(text("DROP INDEX IF EXISTS idx_devices_created_at;"))
        
        # Drop table
        connection.execute(text("DROP TABLE IF EXISTS devices;"))
        
        # Drop enums
        connection.execute(text("DROP TYPE IF EXISTS devicetype;"))
        connection.execute(text("DROP TYPE IF EXISTS sessionstatus;"))
        
        connection.commit()
        print("⚠️ Devices table and enums dropped (rollback)")
