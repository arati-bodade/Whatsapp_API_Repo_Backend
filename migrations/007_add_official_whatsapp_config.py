"""
Official WhatsApp Config Migration

Creates tables for official WhatsApp Cloud API configuration,
templates, and webhook logging.
"""

from sqlalchemy import create_engine, text
from core.config import settings


def upgrade():
    """Create official WhatsApp config tables."""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as connection:
        # Create official_whatsapp_configs table
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS official_whatsapp_configs (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL UNIQUE,
                business_number VARCHAR(20) NOT NULL,
                waba_id VARCHAR(100) NOT NULL,
                phone_number_id VARCHAR(100) NOT NULL,
                access_token VARCHAR(500) NOT NULL,
                template_status VARCHAR(50) NOT NULL DEFAULT 'pending',
                is_active BOOLEAN DEFAULT TRUE,
                webhook_config JSONB,
                api_settings JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """))
        
        # Create whatsapp_templates table
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS whatsapp_templates (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL,
                template_name VARCHAR(100) NOT NULL,
                template_status VARCHAR(50) NOT NULL,
                category VARCHAR(50) NOT NULL,
                language VARCHAR(10) NOT NULL,
                content TEXT NOT NULL,
                meta_template_id VARCHAR(100),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """))
        
        # Create whatsapp_webhook_logs table
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS whatsapp_webhook_logs (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL,
                webhook_event JSONB NOT NULL,
                event_type VARCHAR(50) NOT NULL,
                processed BOOLEAN DEFAULT FALSE,
                error_message TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """))
        
        # Create indexes for better performance
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_official_whatsapp_user_id ON official_whatsapp_configs(user_id);"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_official_whatsapp_phone_number ON official_whatsapp_configs(business_number);"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_official_whatsapp_waba_id ON official_whatsapp_configs(waba_id);"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_whatsapp_templates_user_id ON whatsapp_templates(user_id);"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_whatsapp_templates_name ON whatsapp_templates(template_name);"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_whatsapp_webhook_logs_user_id ON whatsapp_webhook_logs(user_id);"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_whatsapp_webhook_logs_event_type ON whatsapp_webhook_logs(event_type);"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_whatsapp_webhook_logs_created_at ON whatsapp_webhook_logs(created_at);"))
        
        # Create trigger to update updated_at column
        connection.execute(text("""
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ language 'plpgsql';
        """))
        
        connection.execute(text("""
            CREATE TRIGGER update_official_whatsapp_updated_at 
                BEFORE UPDATE ON official_whatsapp_configs 
                FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        """))
        
        connection.execute(text("""
            CREATE TRIGGER update_whatsapp_templates_updated_at 
                BEFORE UPDATE ON whatsapp_templates 
                FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        """))
        
        connection.commit()
        print("✅ Official WhatsApp config tables created successfully")


def downgrade():
    """Remove the official WhatsApp config tables (rollback)."""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as connection:
        # Drop triggers
        connection.execute(text("DROP TRIGGER IF EXISTS update_official_whatsapp_updated_at ON official_whatsapp_configs;"))
        connection.execute(text("DROP TRIGGER IF EXISTS update_whatsapp_templates_updated_at ON whatsapp_templates;"))
        
        # Drop tables
        connection.execute(text("DROP TABLE IF EXISTS whatsapp_webhook_logs;"))
        connection.execute(text("DROP TABLE IF EXISTS whatsapp_templates;"))
        connection.execute(text("DROP TABLE IF EXISTS official_whatsapp_configs;"))
        
        connection.commit()
        print("⚠️ Official WhatsApp config tables dropped (rollback)")
