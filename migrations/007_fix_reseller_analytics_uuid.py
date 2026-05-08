#!/usr/bin/env python3

"""
Migration: Fix reseller_analytics UUID type mismatch
Convert VARCHAR reseller_id to UUID to match User model
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def upgrade():
    """Convert VARCHAR to UUID for reseller_analytics tables."""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as connection:
        # Start transaction
        trans = connection.begin()
        
        try:
            logger.info("Starting UUID migration for reseller_analytics...")
            
            # Drop foreign key constraints
            connection.execute(text("""
                ALTER TABLE reseller_analytics 
                DROP CONSTRAINT IF EXISTS reseller_analytics_reseller_id_fkey;
            """))
            
            connection.execute(text("""
                ALTER TABLE business_user_analytics 
                DROP CONSTRAINT IF EXISTS business_user_analytics_reseller_id_fkey;
            """))
            
            connection.execute(text("""
                ALTER TABLE business_user_analytics 
                DROP CONSTRAINT IF EXISTS business_user_analytics_business_user_id_fkey;
            """))
            
            # Convert columns to UUID
            connection.execute(text("""
                ALTER TABLE reseller_analytics 
                ALTER COLUMN reseller_id TYPE UUID USING reseller_id::UUID;
            """))
            
            connection.execute(text("""
                ALTER TABLE business_user_analytics 
                ALTER COLUMN reseller_id TYPE UUID USING reseller_id::UUID;
            """))
            
            connection.execute(text("""
                ALTER TABLE business_user_analytics 
                ALTER COLUMN business_user_id TYPE UUID USING business_user_id::UUID;
            """))
            
            # Recreate foreign key constraints
            connection.execute(text("""
                ALTER TABLE reseller_analytics 
                ADD CONSTRAINT reseller_analytics_reseller_id_fkey 
                FOREIGN KEY (reseller_id) REFERENCES resellers(user_id);
            """))
            
            connection.execute(text("""
                ALTER TABLE business_user_analytics 
                ADD CONSTRAINT business_user_analytics_reseller_id_fkey 
                FOREIGN KEY (reseller_id) REFERENCES resellers(user_id);
            """))
            
            connection.execute(text("""
                ALTER TABLE business_user_analytics 
                ADD CONSTRAINT business_user_analytics_business_user_id_fkey 
                FOREIGN KEY (business_user_id) REFERENCES businesses(busi_user_id);
            """))
            
            # Commit transaction
            trans.commit()
            logger.info("✅ UUID migration completed successfully!")
            
        except Exception as e:
            trans.rollback()
            logger.error(f"❌ Migration failed: {e}")
            raise

def downgrade():
    """Revert UUID back to VARCHAR."""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as connection:
        trans = connection.begin()
        
        try:
            logger.info("Starting downgrade to VARCHAR...")
            
            # Drop constraints
            connection.execute(text("""
                ALTER TABLE reseller_analytics 
                DROP CONSTRAINT IF EXISTS reseller_analytics_reseller_id_fkey;
            """))
            
            connection.execute(text("""
                ALTER TABLE business_user_analytics 
                DROP CONSTRAINT IF EXISTS business_user_analytics_reseller_id_fkey;
            """))
            
            connection.execute(text("""
                ALTER TABLE business_user_analytics 
                DROP CONSTRAINT IF EXISTS business_user_analytics_business_user_id_fkey;
            """))
            
            # Convert back to VARCHAR
            connection.execute(text("""
                ALTER TABLE reseller_analytics 
                ALTER COLUMN reseller_id TYPE VARCHAR(255);
            """))
            
            connection.execute(text("""
                ALTER TABLE business_user_analytics 
                ALTER COLUMN reseller_id TYPE VARCHAR(255);
            """))
            
            connection.execute(text("""
                ALTER TABLE business_user_analytics 
                ALTER COLUMN business_user_id TYPE VARCHAR(255);
            """))
            
            trans.commit()
            logger.info("✅ Downgrade completed!")
            
        except Exception as e:
            trans.rollback()
            logger.error(f"❌ Downgrade failed: {e}")
            raise

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        downgrade()
    else:
        upgrade()
