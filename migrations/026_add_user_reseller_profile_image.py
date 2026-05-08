#!/usr/bin/env python3

"""
Migration: Add profile_image column to businesses and resellers tables
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
    """Add profile_image column to businesses and resellers tables."""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as connection:
        trans = connection.begin()
        
        try:
            # 1. Update businesses table
            logger.info("Adding profile_image column to businesses table...")
            result = connection.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'businesses' 
                AND column_name = 'profile_image'
            """)).fetchone()
            
            if result:
                logger.info("Column profile_image already exists in businesses, skipping...")
            else:
                connection.execute(text("""
                    ALTER TABLE businesses 
                    ADD COLUMN profile_image VARCHAR(500);
                """))
                logger.info("✅ profile_image column added to businesses successfully!")

            # 2. Update resellers table
            logger.info("Adding profile_image column to resellers table...")
            result = connection.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'resellers' 
                AND column_name = 'profile_image'
            """)).fetchone()
            
            if result:
                logger.info("Column profile_image already exists in resellers, skipping...")
            else:
                connection.execute(text("""
                    ALTER TABLE resellers 
                    ADD COLUMN profile_image VARCHAR(500);
                """))
                logger.info("✅ profile_image column added to resellers successfully!")
            
            trans.commit()
            
        except Exception as e:
            trans.rollback()
            logger.error(f"❌ Migration failed: {e}")
            raise

def downgrade():
    """Remove profile_image column from businesses and resellers tables."""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as connection:
        trans = connection.begin()
        
        try:
            logger.info("Removing profile_image column from businesses and resellers tables...")
            
            connection.execute(text("ALTER TABLE businesses DROP COLUMN IF EXISTS profile_image;"))
            connection.execute(text("ALTER TABLE resellers DROP COLUMN IF EXISTS profile_image;"))
            
            trans.commit()
            logger.info("✅ profile_image columns removed successfully!")
            
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
