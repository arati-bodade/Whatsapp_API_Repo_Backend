#!/usr/bin/env python3

"""
Migration: Fix Database Schema Inconsistencies
This migration fixes all schema inconsistencies between models and database:
1. Fix businesses table primary key from user_id to busi_user_id
2. Fix foreign key references to use correct table names
3. Update constraints to match model relationships
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
    """Fix all database schema inconsistencies."""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as connection:
        trans = connection.begin()
        
        try:
            logger.info("Starting comprehensive database schema fix...")
            
            # 1. Drop existing foreign key constraints
            logger.info("Dropping existing constraints...")
            
            # Drop credit_distributions constraints
            connection.execute(text("""
                ALTER TABLE credit_distributions 
                DROP CONSTRAINT IF EXISTS credit_distributions_from_reseller_id_fkey;
            """))
            
            connection.execute(text("""
                ALTER TABLE credit_distributions 
                DROP CONSTRAINT IF EXISTS credit_distributions_to_business_user_id_fkey;
            """))
            
            # Drop businesses table constraint
            connection.execute(text("""
                ALTER TABLE businesses 
                DROP CONSTRAINT IF EXISTS businesses_parent_reseller_id_fkey;
            """))
            
            # Drop analytics constraints
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
            
            # 2. Clean up orphaned data before fixing constraints
            logger.info("Cleaning up orphaned data...")
            
            # Check if businesses table has user_id or busi_user_id column
            column_check = connection.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'businesses' 
                AND column_name IN ('user_id', 'busi_user_id');
            """)).fetchall()
            
            business_id_column = 'busi_user_id' if any(col[0] == 'busi_user_id' for col in column_check) else 'user_id'
            logger.info(f"Using business ID column: {business_id_column}")
            
            # Remove businesses with invalid parent_reseller_id
            result = connection.execute(text("""
                DELETE FROM businesses 
                WHERE parent_reseller_id NOT IN (SELECT user_id FROM resellers);
            """))
            logger.info(f"Removed {result.rowcount} orphaned business records")
            
            # Remove credit_distributions with invalid references
            result = connection.execute(text(f"""
                DELETE FROM credit_distributions 
                WHERE from_reseller_id NOT IN (SELECT user_id FROM resellers)
                OR to_business_user_id NOT IN (SELECT {business_id_column} FROM businesses);
            """))
            logger.info(f"Removed {result.rowcount} orphaned credit distribution records")
            
            # Remove analytics with invalid references
            result = connection.execute(text("""
                DELETE FROM reseller_analytics 
                WHERE reseller_id NOT IN (SELECT user_id FROM resellers);
            """))
            logger.info(f"Removed {result.rowcount} orphaned reseller analytics records")
            
            result = connection.execute(text(f"""
                DELETE FROM business_user_analytics 
                WHERE reseller_id NOT IN (SELECT user_id FROM resellers)
                OR business_user_id NOT IN (SELECT {business_id_column} FROM businesses);
            """))
            logger.info(f"Removed {result.rowcount} orphaned business user analytics records")
            
            # 3. Fix businesses table primary key if needed
            logger.info("Checking businesses table primary key...")
            
            # Check if column exists and is primary key
            result = connection.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'businesses' 
                AND column_name = 'user_id';
            """)).fetchone()
            
            if result:
                logger.info("Fixing businesses table primary key...")
                # Rename user_id to busi_user_id
                connection.execute(text("""
                    ALTER TABLE businesses RENAME COLUMN user_id TO busi_user_id;
                """))
                
                # Recreate primary key constraint
                connection.execute(text("""
                    ALTER TABLE businesses DROP CONSTRAINT IF EXISTS businesses_pkey;
                """))
                
                connection.execute(text("""
                    ALTER TABLE businesses ADD CONSTRAINT businesses_pkey PRIMARY KEY (busi_user_id);
                """))
            
            # 4. Recreate all foreign key constraints with correct references
            logger.info("Recreating foreign key constraints...")
            
            # Fix businesses parent_reseller_id constraint
            connection.execute(text("""
                ALTER TABLE businesses 
                ADD CONSTRAINT businesses_parent_reseller_id_fkey 
                FOREIGN KEY (parent_reseller_id) REFERENCES resellers(user_id);
            """))
            
            # Fix credit_distributions constraints
            connection.execute(text("""
                ALTER TABLE credit_distributions 
                ADD CONSTRAINT credit_distributions_from_reseller_id_fkey 
                FOREIGN KEY (from_reseller_id) REFERENCES resellers(user_id);
            """))
            
            connection.execute(text("""
                ALTER TABLE credit_distributions 
                ADD CONSTRAINT credit_distributions_to_business_user_id_fkey 
                FOREIGN KEY (to_business_user_id) REFERENCES businesses(busi_user_id);
            """))
            
            # Fix analytics constraints
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
            
            # 5. Update indexes if needed
            logger.info("Updating indexes...")
            
            # Drop and recreate indexes with new column name
            connection.execute(text("DROP INDEX IF EXISTS idx_businesses_parent_reseller;"))
            connection.execute(text("CREATE INDEX idx_businesses_parent_reseller ON businesses(parent_reseller_id);"))
            
            trans.commit()
            logger.info("✅ Database schema fix completed successfully!")
            
        except Exception as e:
            trans.rollback()
            logger.error(f"❌ Migration failed: {e}")
            raise

def downgrade():
    """Revert the schema changes."""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as connection:
        trans = connection.begin()
        
        try:
            logger.info("Starting schema downgrade...")
            
            # Drop all constraints
            connection.execute(text("ALTER TABLE businesses DROP CONSTRAINT IF EXISTS businesses_parent_reseller_id_fkey;"))
            connection.execute(text("ALTER TABLE credit_distributions DROP CONSTRAINT IF EXISTS credit_distributions_from_reseller_id_fkey;"))
            connection.execute(text("ALTER TABLE credit_distributions DROP CONSTRAINT IF EXISTS credit_distributions_to_business_user_id_fkey;"))
            connection.execute(text("ALTER TABLE reseller_analytics DROP CONSTRAINT IF EXISTS reseller_analytics_reseller_id_fkey;"))
            connection.execute(text("ALTER TABLE business_user_analytics DROP CONSTRAINT IF EXISTS business_user_analytics_reseller_id_fkey;"))
            connection.execute(text("ALTER TABLE business_user_analytics DROP CONSTRAINT IF EXISTS business_user_analytics_business_user_id_fkey;"))
            
            # Rename column back
            connection.execute(text("""
                ALTER TABLE businesses RENAME COLUMN busi_user_id TO user_id;
            """))
            
            # Recreate primary key
            connection.execute(text("ALTER TABLE businesses DROP CONSTRAINT IF EXISTS businesses_pkey;"))
            connection.execute(text("ALTER TABLE businesses ADD CONSTRAINT businesses_pkey PRIMARY KEY (user_id);"))
            
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
