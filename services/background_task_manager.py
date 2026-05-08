"""
Background Task Manager

Production-ready background task management for FastAPI applications.
Ensures non-blocking startup and proper error handling for background services.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional
from sqlalchemy.orm import Session
from db.session import get_db

logger = logging.getLogger(__name__)


class BackgroundTaskManager:
    """
    Manages background tasks with proper database session handling
    and error recovery mechanisms.
    """
    
    def __init__(self):
        self._running = False
        self._polling_task: Optional[asyncio.Task] = None
        
    async def run_google_sheets_polling(self, interval_seconds: int = 30):
        """
        Run Google Sheets polling in a properly managed background task.
        
        This method:
        1. Creates fresh database sessions for each polling cycle
        2. Handles connection errors gracefully
        3. Prevents blocking of the main FastAPI application
        4. Implements proper error recovery
        """
        self._running = True
        logger.info(f"Starting Google Sheets polling (interval: {interval_seconds}s)")
        
        while self._running:
            try:
                # Create fresh database session for this polling cycle
                db = next(get_db())
                
                try:
                    # Import and process triggers
                    from services.google_sheets_automation_unofficial_only import GoogleSheetsAutomationServiceUnofficial
                    automation_service = GoogleSheetsAutomationServiceUnofficial(db)
                    
                    # Process all active triggers
                    await automation_service.process_all_active_triggers()
                    
                finally:
                    # Always close the database session
                    db.close()
                
                # Wait for next polling cycle
                await asyncio.sleep(interval_seconds)
                
            except asyncio.CancelledError:
                logger.info("Google Sheets polling cancelled gracefully")
                break
                
            except Exception as e:
                logger.error(f"Error in Google Sheets polling cycle: {e}")
                
                # Wait shorter interval before retrying after error
                try:
                    await asyncio.sleep(min(10, interval_seconds))
                except asyncio.CancelledError:
                    logger.info("Google Sheets polling cancelled during error recovery")
                    break
        
        self._running = False
        logger.info("Google Sheets polling stopped")
    
    def stop(self):
        """Stop the background polling gracefully"""
        self._running = False
        if self._polling_task and not self._polling_task.done():
            self._polling_task.cancel()


# SafeBackgroundService removed due to connection pool exhaustion issues
# The threaded approach with loop.run_until_complete creates new event loops
# that compete for database connections, causing pool exhaustion.
# Use the async BackgroundTaskManager instead.
