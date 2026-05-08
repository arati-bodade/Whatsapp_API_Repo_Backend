#!/usr/bin/env python3

"""
Migration script to add CASCADE DELETE to group_contacts table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from db.session import get_db
from core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_cascade_delete():
    """Add CASCADE DELETE to foreign keys in group_contacts table"""
    
    try:
        # Get database URL from settings
        database_url = settings.DATABASE_URL
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()
            
            try:
                logger.info("Adding CASCADE DELETE to group_contacts table...")
                
                # Drop existing foreign key constraints
                logger.info("Dropping existing foreign key constraints...")
                conn.execute(text("""
                    ALTER TABLE group_contacts 
                    DROP CONSTRAINT IF EXISTS group_contacts_group_id_fkey
                """))
                
                conn.execute(text("""
                    ALTER TABLE group_contacts 
                    DROP CONSTRAINT IF EXISTS group_contacts_contact_id_fkey
                """))
                
                # Add new foreign key constraints with CASCADE DELETE
                logger.info("Adding new foreign key constraints with CASCADE DELETE...")
                conn.execute(text("""
                    ALTER TABLE group_contacts 
                    ADD CONSTRAINT group_contacts_group_id_fkey 
                    FOREIGN KEY (group_id) 
                    REFERENCES contact_groups(group_id) 
                    ON DELETE CASCADE
                """))
                
                conn.execute(text("""
                    ALTER TABLE group_contacts 
                    ADD CONSTRAINT group_contacts_contact_id_fkey 
                    FOREIGN KEY (contact_id) 
                    REFERENCES contacts(contact_id) 
                    ON DELETE CASCADE
                """))
                
                # Commit transaction
                trans.commit()
                logger.info("✅ CASCADE DELETE successfully added to group_contacts table!")
                
            except Exception as e:
                # Rollback on error
                trans.rollback()
                logger.error(f"❌ Error adding CASCADE DELETE: {e}")
                raise
                
    except Exception as e:
        logger.error(f"❌ Database connection error: {e}")
        raise

if __name__ == "__main__":
    add_cascade_delete()
