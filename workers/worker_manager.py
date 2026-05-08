import asyncio
import logging
from typing import Dict, Optional

logger = logging.getLogger("WORKER_MANAGER")

# Centralized registry for active campaign workers
# { campaign_id: asyncio.Task }
campaign_workers: Dict[str, asyncio.Task] = {}

# Global lock to synchronize worker creation/stopping
campaign_lock = asyncio.Lock()

async def is_worker_active(campaign_id: str) -> bool:
    """Check if a worker task is currently active for a campaign."""
    async with campaign_lock:
        task = campaign_workers.get(campaign_id)
        if task and not task.done():
            return True
        # If task exists but is done, clean it up
        if task and task.done():
            campaign_workers.pop(campaign_id, None)
    return False

async def register_worker(campaign_id: str, task: asyncio.Task):
    """Register a new worker task for a campaign."""
    async with campaign_lock:
        campaign_workers[campaign_id] = task
        logger.info(f"Registered worker for campaign {campaign_id}")

async def unregister_worker(campaign_id: str):
    """Unregister a worker task for a campaign."""
    async with campaign_lock:
        campaign_workers.pop(campaign_id, None)
        logger.info(f"Unregistered worker for campaign {campaign_id}")

def get_active_tasks_count() -> int:
    """Return the total number of currently active workers."""
    return len([t for t in campaign_workers.values() if not t.done()])
