#!/usr/bin/env python3

"""
Migration: Fix devices table user_id column name
Change user_id to busi_user_id to match model definition
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
    """Rename user_id to busi_user_id in devices table."""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as connection:
        trans = connection.begin()
        
        try:
            logger.info("Renaming user_id to busi_user_id in devices table...")
            
            # Check if column exists and rename it
            connection.execute(text("""
                ALTER TABLE devices 
                RENAME COLUMN user_id TO busi_user_id;
            """))
            
            trans.commit()
            logger.info("✅ Column renamed successfully!")
            
        except Exception as e:
            trans.rollback()
            logger.error(f"❌ Migration failed: {e}")
            raise

def downgrade():
    """Revert busi_user_id back to user_id in devices table."""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as connection:
        trans = connection.begin()
        
        try:
            logger.info("Reverting busi_user_id to user_id in devices table...")
            
            connection.execute(text("""
                ALTER TABLE devices 
                RENAME COLUMN busi_user_id TO user_id;
            """))
            
            trans.commit()
            logger.info("✅ Column reverted successfully!")
            
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
