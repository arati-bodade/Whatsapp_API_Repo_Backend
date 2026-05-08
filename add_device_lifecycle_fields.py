#!/usr/bin/env python3
"""
Migration script to add device lifecycle fields to the devices table
"""

import sqlalchemy
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/whatsapp_platform")

def migrate_device_lifecycle():
    """Add new columns to devices table for lifecycle management"""
    
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Start transaction
        trans = conn.begin()
        
        try:
            print("Adding device lifecycle fields...")
            
            # Add is_active column if not exists
            conn.execute(text("""
                DO $$ 
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='devices' AND column_name='is_active'
                    ) THEN
                        ALTER TABLE devices ADD COLUMN is_active BOOLEAN DEFAULT TRUE NOT NULL;
                        RAISE NOTICE 'Added is_active column';
                    END IF;
                END $$;
            """))
            
            # Add disconnected_at column if not exists
            conn.execute(text("""
                DO $$ 
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='devices' AND column_name='disconnected_at'
                    ) THEN
                        ALTER TABLE devices ADD COLUMN disconnected_at TIMESTAMP WITH TIME ZONE;
                        RAISE NOTICE 'Added disconnected_at column';
                    END IF;
                END $$;
            """))
            
            # Update session_status enum to include 'logged_out'
            conn.execute(text("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_enum 
                        WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'sessionstatus')
                        AND enumlabel = 'logged_out'
                    ) THEN
                        ALTER TYPE sessionstatus ADD VALUE 'logged_out';
                        RAISE NOTICE 'Added logged_out to sessionstatus enum';
                    END IF;
                END $$;
            """))
            
            # Commit transaction
            trans.commit()
            print("✅ Device lifecycle migration completed successfully!")
            
        except Exception as e:
            # Rollback on error
            trans.rollback()
            print(f"❌ Migration failed: {str(e)}")
            raise

if __name__ == "__main__":
    migrate_device_lifecycle()
