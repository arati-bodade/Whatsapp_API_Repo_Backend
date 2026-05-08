from sqlalchemy import text
from db.base import engine

def upgrade():
    with engine.connect() as connection:
        # 1. Update reseller_analytics table
        # Add unique constraint to reseller_id if it doesn't exist
        try:
            connection.execute(text("""
                ALTER TABLE reseller_analytics 
                ADD CONSTRAINT uq_reseller_analytics_reseller_id UNIQUE (reseller_id);
            """))
        except Exception as e:
            print(f"Constraint might already exist: {e}")

        # Ensure business_user_stats is JSONB/JSON (postgres)
        # It was defined as JSON in model, ensure column exists and type is correct
        # Existing migration 006 created it, so it should be fine.

        # 2. Create business_user_analytics table if not exists
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS business_user_analytics (
                id SERIAL PRIMARY KEY,
                reseller_id UUID NOT NULL,
                business_user_id UUID NOT NULL,
                business_name VARCHAR NOT NULL,
                credits_allocated INTEGER NOT NULL DEFAULT 0,
                credits_used INTEGER NOT NULL DEFAULT 0,
                credits_remaining INTEGER NOT NULL DEFAULT 0,
                messages_sent INTEGER NOT NULL DEFAULT 0,
                generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                CONSTRAINT fk_bua_reseller FOREIGN KEY (reseller_id) REFERENCES resellers(user_id),
                CONSTRAINT fk_bua_business_user FOREIGN KEY (business_user_id) REFERENCES businesses(busi_user_id),
                CONSTRAINT uq_bua_business_user_id UNIQUE (business_user_id)
            );
        """))
        
        # Create indexes for business_user_analytics
        connection.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_business_user_analytics_id ON business_user_analytics (id);
            CREATE INDEX IF NOT EXISTS ix_business_user_analytics_reseller_id ON business_user_analytics (reseller_id);
            CREATE INDEX IF NOT EXISTS ix_business_user_analytics_business_user_id ON business_user_analytics (business_user_id);
        """))

        connection.commit()
