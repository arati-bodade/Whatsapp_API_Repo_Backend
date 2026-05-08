#!/usr/bin/env python3

"""
Migration: Add profile_image column to master_admins table
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
    """Add profile_image column to master_admins table."""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as connection:
        trans = connection.begin()
        
        try:
            logger.info("Adding profile_image column to master_admins table...")
            
            # Check if column already exists
            result = connection.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'master_admins' 
                AND column_name = 'profile_image'
            """)).fetchone()
            
            if result:
                logger.info("Column profile_image already exists, skipping...")
            else:
                connection.execute(text("""
                    ALTER TABLE master_admins 
                    ADD COLUMN profile_image VARCHAR(500);
                """))
                logger.info("✅ profile_image column added successfully!")
            
            trans.commit()
            
        except Exception as e:
            trans.rollback()
            logger.error(f"❌ Migration failed: {e}")
            raise

def downgrade():
    """Remove profile_image column from master_admins table."""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as connection:
        trans = connection.begin()
        
        try:
            logger.info("Removing profile_image column from master_admins table...")
            
            connection.execute(text("""
                ALTER TABLE master_admins 
                DROP COLUMN IF EXISTS profile_image;
            """))
            
            trans.commit()
            logger.info("✅ profile_image column removed successfully!")
            
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
