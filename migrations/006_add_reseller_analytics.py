"""
Reseller Analytics Migration

Creates tables for reseller analytics and business user analytics
to track performance metrics and dashboard data.
"""

from sqlalchemy import create_engine, text
from core.config import settings


def upgrade():
    """Create reseller analytics tables."""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as connection:
        # Create reseller_analytics table
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS reseller_analytics (
                id SERIAL PRIMARY KEY,
                reseller_id VARCHAR(255) NOT NULL,
                total_credits_purchased INTEGER NOT NULL DEFAULT 0,
                total_credits_distributed INTEGER NOT NULL DEFAULT 0,
                total_credits_used INTEGER NOT NULL DEFAULT 0,
                remaining_credits INTEGER NOT NULL DEFAULT 0,
                business_user_stats JSONB NOT NULL DEFAULT '[]',
                generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """))
        
        # Create business_user_analytics table
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS business_user_analytics (
                id SERIAL PRIMARY KEY,
                reseller_id VARCHAR(255) NOT NULL,
                business_user_id VARCHAR(255) NOT NULL,
                business_name VARCHAR(255) NOT NULL,
                credits_allocated INTEGER NOT NULL DEFAULT 0,
                credits_used INTEGER NOT NULL DEFAULT 0,
                credits_remaining INTEGER NOT NULL DEFAULT 0,
                messages_sent INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """))
        
        # Create indexes for better performance
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_reseller_analytics_reseller_id ON reseller_analytics(reseller_id);"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_reseller_analytics_generated_at ON reseller_analytics(generated_at);"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_business_analytics_reseller_id ON business_user_analytics(reseller_id);"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_business_analytics_business_user_id ON business_user_analytics(business_user_id);"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_business_analytics_reseller_business ON business_user_analytics(reseller_id, business_user_id);"))
        
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
            CREATE TRIGGER update_reseller_analytics_updated_at 
                BEFORE UPDATE ON reseller_analytics 
                FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        """))
        
        connection.execute(text("""
            CREATE TRIGGER update_business_analytics_updated_at 
                BEFORE UPDATE ON business_user_analytics 
                FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        """))
        
        connection.commit()
        print("✅ Reseller analytics tables created successfully")


def downgrade():
    """Remove the reseller analytics tables (rollback)."""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as connection:
        # Drop triggers
        connection.execute(text("DROP TRIGGER IF EXISTS update_reseller_analytics_updated_at ON reseller_analytics;"))
        connection.execute(text("DROP TRIGGER IF EXISTS update_business_analytics_updated_at ON business_user_analytics;"))
        
        # Drop tables
        connection.execute(text("DROP TABLE IF EXISTS business_user_analytics;"))
        connection.execute(text("DROP TABLE IF EXISTS reseller_analytics;"))
        
        connection.commit()
        print("⚠️ Reseller analytics tables dropped (rollback)")
