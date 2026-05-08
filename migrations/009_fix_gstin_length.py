#!/usr/bin/env python3

"""
Migration: Fix GSTIN field length
Increase GSTIN field from VARCHAR(15) to VARCHAR(20) to match schema validation
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
    """Increase GSTIN field length to 20 characters."""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as connection:
        trans = connection.begin()
        
        try:
            logger.info("Increasing GSTIN field length...")
            
            # Update resellers table
            connection.execute(text("""
                ALTER TABLE resellers 
                ALTER COLUMN gstin TYPE VARCHAR(20);
            """))
            
            # Update businesses table  
            connection.execute(text("""
                ALTER TABLE businesses 
                ALTER COLUMN gstin TYPE VARCHAR(20);
            """))
            
            trans.commit()
            logger.info("✅ GSTIN field length updated successfully!")
            
        except Exception as e:
            trans.rollback()
            logger.error(f"❌ Migration failed: {e}")
            raise

def downgrade():
    """Revert GSTIN field length back to 15 characters."""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as connection:
        trans = connection.begin()
        
        try:
            logger.info("Reverting GSTIN field length...")
            
            # Check if any data exceeds 15 characters
            result = connection.execute(text("""
                SELECT COUNT(*) FROM resellers WHERE LENGTH(gstin) > 15
            """)).fetchone()[0]
            
            if result > 0:
                logger.warning(f"Found {result} records with GSTIN longer than 15 characters")
                logger.warning("Data loss may occur during downgrade")
            
            # Update resellers table
            connection.execute(text("""
                ALTER TABLE resellers 
                ALTER COLUMN gstin TYPE VARCHAR(20);
            """))
            
            # Update businesses table
            connection.execute(text("""
                ALTER TABLE businesses 
                ALTER COLUMN gstin TYPE VARCHAR(20);
            """))
            
            trans.commit()
            logger.info("✅ GSTIN field length reverted successfully!")
            
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
