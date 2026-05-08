import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from db.session import SessionLocal
from models.device import Device
from tasks.scheduler import scheduler

logger = logging.getLogger("TASKS")

async def keep_engine_alive():
    """
    Pings the WhatsApp engine periodically to prevent Render free tier from sleeping (15m inactivity).
    """
    from services.whatsapp_engine_service import WhatsAppEngineService
    from db.session import SessionLocal
    
    with SessionLocal() as db:
        engine = WhatsAppEngineService(db)
        try:
            logger.info("📡 [KEEP_ALIVE] Pinging WhatsApp Engine to prevent sleep...")
            # Use light health check
            engine.check_engine_reachable()
        except Exception as e:
            logger.error(f"❌ [KEEP_ALIVE] Ping failed: {str(e)}")

async def daily_device_reset():
    """
    Resets the daily_sent_count for all devices at midnight.
    """
    with SessionLocal() as db:
        try:
            # Check if column exists, if not, ignore or create. Let's execute raw SQL and catch exception if column missing.
            db.execute("ALTER TABLE devices ADD COLUMN IF NOT EXISTS daily_sent_count INTEGER DEFAULT 0")
            db.commit()
            
            # Now reset
            db.execute("UPDATE devices SET daily_sent_count = 0")
            db.commit()
            logger.info("✅ Successfully reset daily_sent_count for all devices.")
        except Exception as e:
            logger.error(f"Failed to reset device daily stats: {str(e)}")
            if db.in_transaction():
                db.rollback()

def schedule_daily_tasks():
    # 🔥 PING ENGINE every 10 minutes (prevents 15m Render sleep) - DISABLED as requested
    # scheduler.add_task(keep_engine_alive, 600)
    
    # Schedule daily stats reset
    scheduler.add_task(daily_device_reset, 86400)
    logger.info("Scheduled background tasks (Daily Reset).")
