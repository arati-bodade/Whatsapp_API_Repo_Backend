from sqlalchemy import create_engine, text
from core.config import settings


def upgrade():
    """Add device_sessions table"""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as connection:
        # Create device_sessions table
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS device_sessions (
                session_id VARCHAR(50) PRIMARY KEY,
                device_id VARCHAR(50) NOT NULL,
                session_token TEXT NOT NULL,
                is_valid BOOLEAN DEFAULT TRUE NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                last_active TIMESTAMP WITH TIME ZONE,
                FOREIGN KEY (device_id) REFERENCES devices(device_id) ON DELETE CASCADE
            );
        """))
        
        # Create indexes
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_device_sessions_session_id ON device_sessions(session_id);"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_device_sessions_device_id ON device_sessions(device_id);"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_device_sessions_is_valid ON device_sessions(is_valid);"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_device_sessions_expires_at ON device_sessions(expires_at);"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_device_sessions_last_active ON device_sessions(last_active);"))
        
        connection.commit()
        print("✅ Device sessions table created successfully")


def downgrade():
    """Remove device_sessions table"""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as connection:
        connection.execute(text("DROP TABLE IF EXISTS device_sessions CASCADE;"))
        connection.commit()
        print("✅ Device sessions table dropped successfully")
