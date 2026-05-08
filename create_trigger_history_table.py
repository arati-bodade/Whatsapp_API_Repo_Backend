#!/usr/bin/env python3
"""
Create missing google_sheet_trigger_history table
"""

import logging
from sqlalchemy import text
from db.session import SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_trigger_history_table():
    """Create the missing google_sheet_trigger_history table"""
    logger.info("🔧 CREATING GOOGLE_SHEET_TRIGGER_HISTORY TABLE")
    logger.info("=" * 60)
    
    db = SessionLocal()
    try:
        # SQL to create the table
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS google_sheet_trigger_history (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            sheet_id UUID NOT NULL REFERENCES google_sheets(id) ON DELETE CASCADE,
            trigger_id VARCHAR(255) NOT NULL,
            row_number INTEGER,
            phone_number VARCHAR(50),
            message_content TEXT,
            status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
            error_message TEXT,
            triggered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Create indexes for better performance
        CREATE INDEX IF NOT EXISTS idx_google_sheet_trigger_history_sheet_id 
            ON google_sheet_trigger_history(sheet_id);
            
        CREATE INDEX IF NOT EXISTS idx_google_sheet_trigger_history_triggered_at 
            ON google_sheet_trigger_history(triggered_at DESC);
            
        CREATE INDEX IF NOT EXISTS idx_google_sheet_trigger_history_status 
            ON google_sheet_trigger_history(status);
        """
        
        logger.info("🔧 Creating google_sheet_trigger_history table...")
        db.execute(text(create_table_sql))
        db.commit()
        logger.info("✅ Table created successfully!")
        
        # Verify table exists
        try:
            result = db.execute(text("SELECT COUNT(*) FROM google_sheet_trigger_history"))
            count = result.scalar()
            logger.info(f"📊 Current record count: {count}")
        except Exception as e:
            logger.error(f"❌ Error verifying table: {e}")
            return False
        
        # Test inserting a sample record
        logger.info("🧪 Testing table with sample record...")
        sample_sql = """
        INSERT INTO google_sheet_trigger_history (
            sheet_id, trigger_id, phone_number, message_content, status
        ) VALUES (
            gen_random_uuid(), 'test-trigger', '+1234567890', 'Test message', 'TEST'
        );
        """
        
        db.execute(text(sample_sql))
        db.commit()
        logger.info("✅ Sample record inserted successfully!")
        
        # Clean up test record
        db.execute(text("DELETE FROM google_sheet_trigger_history WHERE status = 'TEST'"))
        db.commit()
        logger.info("🧹 Test record cleaned up!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creating table: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def verify_table_structure():
    """Verify the table structure"""
    logger.info("\n🔍 VERIFYING TABLE STRUCTURE")
    logger.info("=" * 40)
    
    db = SessionLocal()
    try:
        # Get table info
        result = db.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'google_sheet_trigger_history'
            ORDER BY ordinal_position
        """))
        
        columns = result.fetchall()
        
        logger.info("📋 Table columns:")
        for col in columns:
            logger.info(f"   {col[0]}: {col[1]} (nullable: {col[2]})")
        
        # Check foreign key
        try:
            result = db.execute(text("""
                SELECT tc.constraint_name, tc.constraint_type, 
                       kcu.column_name, ccu.table_name AS foreign_table_name
                FROM information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY' 
                    AND tc.table_name = 'google_sheet_trigger_history'
            """))
            
            fks = result.fetchall()
            logger.info("\n🔗 Foreign keys:")
            for fk in fks:
                logger.info(f"   {fk[0]}: {fk[2]} → {fk[3]}")
                
        except Exception as e:
            logger.warning(f"⚠️ Could not check foreign keys: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error verifying table: {e}")
        return False
    finally:
        db.close()

def show_fix_summary():
    """Show fix summary"""
    logger.info("\n✅ TRIGGER HISTORY TABLE FIX SUMMARY")
    logger.info("=" * 50)
    
    logger.info("""
🔧 ISSUE IDENTIFIED:
- google_sheet_trigger_history table was missing
- Trigger history API was failing
- No execution records could be stored
- Refresh button appeared to not work

🔧 SOLUTION IMPLEMENTED:
- Created google_sheet_trigger_history table
- Added proper indexes for performance
- Added foreign key constraints
- Tested table functionality

📋 TABLE STRUCTURE:
┌─────────────────────────────────────────────────────────────┐
│ Column          │ Type           │ Nullable │ Description           │
├─────────────────────────────────────────────────────────────┤
│ id              │ UUID           │ No       │ Primary key           │
│ sheet_id        │ UUID           │ No       │ Foreign key to sheets │
│ trigger_id      │ VARCHAR(255)   │ No       │ Trigger identifier    │
│ row_number      │ INTEGER        │ Yes      │ Sheet row number     │
│ phone_number    │ VARCHAR(50)    │ Yes      │ Recipient phone      │
│ message_content │ TEXT           │ Yes      │ Message sent         │
│ status          │ VARCHAR(50)    │ No       │ Execution status     │
│ error_message   │ TEXT           │ Yes      │ Error details        │
│ triggered_at    │ TIMESTAMP      │ Yes      │ Execution time       │
│ created_at      │ TIMESTAMP      │ Yes      │ Record creation     │
│ updated_at      │ TIMESTAMP      │ Yes      │ Record update       │
└─────────────────────────────────────────────────────────────┘

🔍 INDEXES CREATED:
- idx_google_sheet_trigger_history_sheet_id
- idx_google_sheet_trigger_history_triggered_at  
- idx_google_sheet_trigger_history_status

🚀 EXPECTED RESULTS:
- Trigger history API should work correctly
- Refresh button should load data
- Execution records should be stored
- Trigger performance should be good

🎯 NEXT STEPS:
1. Restart the backend server
2. Test trigger execution
3. Verify trigger history population
4. Test refresh button functionality
5. Monitor logs for proper execution

✅ FIX COMPLETE!
The trigger history system should now work correctly.
    """)

if __name__ == "__main__":
    success = create_trigger_history_table()
    
    if success:
        verify_table_structure()
        show_fix_summary()
        logger.info("\n🎉 TRIGGER HISTORY TABLE FIX COMPLETE!")
    else:
        logger.info("\n❌ TABLE CREATION FAILED")
        logger.info("🔧 Check database permissions and connection")
