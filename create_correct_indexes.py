#!/usr/bin/env python3
"""
Script to create correct indexes for the database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
import logging

# Direct database URL
DATABASE_URL = "postgresql://whatsapp_platform_fn0k_user:AbHezwfAs553dVCy33wfHzsGMVJbf8M0@dpg-d6oh8tfafjfc7386oii0-a.oregon-postgres.render.com/whatsapp_platform_fn0k"

# Create engine with the new database URL
engine = create_engine(DATABASE_URL)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_correct_indexes():
    """Create additional indexes for performance"""
    indexes = [
        # Devices indexes
        "CREATE INDEX IF NOT EXISTS idx_devices_busi_user_id ON devices(busi_user_id);",
        "CREATE INDEX IF NOT EXISTS idx_devices_session_status ON devices(session_status);",
        "CREATE INDEX IF NOT EXISTS idx_devices_device_type ON devices(device_type);",
        
        # Messages indexes
        "CREATE INDEX IF NOT EXISTS idx_messages_busi_user_id ON messages(busi_user_id);",
        "CREATE INDEX IF NOT EXISTS idx_messages_sender_number ON messages(sender_number);",
        "CREATE INDEX IF NOT EXISTS idx_messages_receiver_number ON messages(receiver_number);",
        "CREATE INDEX IF NOT EXISTS idx_messages_status ON messages(status);",
        "CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);",
        
        # Campaigns indexes
        "CREATE INDEX IF NOT EXISTS idx_campaigns_busi_user_id ON campaigns(busi_user_id);",
        "CREATE INDEX IF NOT EXISTS idx_campaigns_status ON campaigns(status);",
        
        # Google Sheets indexes
        "CREATE INDEX IF NOT EXISTS idx_google_sheets_user_id ON google_sheets(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_google_sheets_status ON google_sheets(status);",
        
        # Google Sheet Triggers indexes
        "CREATE INDEX IF NOT EXISTS idx_google_sheet_triggers_sheet_id ON google_sheet_triggers(sheet_id);",
        "CREATE INDEX IF NOT EXISTS idx_google_sheet_triggers_is_enabled ON google_sheet_triggers(is_enabled);",
        
        # Sheet Trigger History indexes
        "CREATE INDEX IF NOT EXISTS idx_sheet_trigger_history_sheet_id ON sheet_trigger_history(sheet_id);",
        "CREATE INDEX IF NOT EXISTS idx_sheet_trigger_history_status ON sheet_trigger_history(status);",
        "CREATE INDEX IF NOT EXISTS idx_sheet_trigger_history_triggered_at ON sheet_trigger_history(triggered_at);",
        
        # WhatsApp Inbox indexes
        "CREATE INDEX IF NOT EXISTS idx_whatsapp_inbox_busi_user_id ON whatsapp_inbox(busi_user_id);",
        "CREATE INDEX IF NOT EXISTS idx_whatsapp_inbox_phone_number ON whatsapp_inbox(phone_number);",
        
        # WhatsApp Messages indexes
        "CREATE INDEX IF NOT EXISTS idx_whatsapp_messages_busi_user_id ON whatsapp_messages(busi_user_id);",
        "CREATE INDEX IF NOT EXISTS idx_whatsapp_messages_device_id ON whatsapp_messages(device_id);",
        "CREATE INDEX IF NOT EXISTS idx_whatsapp_messages_message_type ON whatsapp_messages(message_type);",
        
        # Device Sessions indexes
        "CREATE INDEX IF NOT EXISTS idx_device_sessions_device_id ON device_sessions(device_id);",
        "CREATE INDEX IF NOT EXISTS idx_device_sessions_is_valid ON device_sessions(is_valid);",
        "CREATE INDEX IF NOT EXISTS idx_device_sessions_expires_at ON device_sessions(expires_at);",
        
        # Credit Distributions indexes
        "CREATE INDEX IF NOT EXISTS idx_credit_distributions_reseller_id ON credit_distributions(reseller_id);",
        "CREATE INDEX IF NOT EXISTS idx_credit_distributions_business_id ON credit_distributions(business_id);",
        
        # Message Usage Credit Logs indexes
        "CREATE INDEX IF NOT EXISTS idx_message_usage_credit_logs_busi_user_id ON message_usage_credit_logs(busi_user_id);",
        "CREATE INDEX IF NOT EXISTS idx_message_usage_credit_logs_created_at ON message_usage_credit_logs(created_at);",
    ]
    
    try:
        logger.info("🔧 Creating performance indexes...")
        with engine.connect() as conn:
            for i, index_sql in enumerate(indexes, 1):
                try:
                    conn.execute(text(index_sql))
                    logger.info(f"  ✅ Index {i}/{len(indexes)} created")
                except Exception as e:
                    logger.warning(f"  ⚠️  Index {i}/{len(indexes)} failed: {e}")
            conn.commit()
        logger.info("✅ Performance indexes creation completed!")
        return True
    except Exception as e:
        logger.error(f"❌ Error creating indexes: {e}")
        return False

def show_table_info():
    """Show information about created tables"""
    try:
        with engine.connect() as conn:
            # Get table counts
            result = conn.execute(text("""
                SELECT table_name, 
                       (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name AND table_schema = 'public') as column_count
                FROM information_schema.tables t
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            
            logger.info("📊 Database Tables Summary:")
            for row in result:
                logger.info(f"  📋 {row[0]} ({row[1]} columns)")
                
            # Get total row counts
            result = conn.execute(text("""
                SELECT schemaname,tablename,attname,n_distinct,correlation
                FROM pg_stats 
                WHERE schemaname = 'public'
                ORDER BY tablename,attname;
            """))
            
    except Exception as e:
        logger.error(f"❌ Error getting table info: {e}")

def main():
    """Main function"""
    logger.info("🎯 Creating correct indexes for the database...")
    
    # Show table information
    show_table_info()
    
    # Create indexes
    if create_correct_indexes():
        logger.info("🎉 Database indexing completed successfully!")
    else:
        logger.warning("⚠️  Some indexes may not have been created")
    
    logger.info("📝 Your new PostgreSQL database is fully ready with all tables and indexes!")

if __name__ == "__main__":
    main()
