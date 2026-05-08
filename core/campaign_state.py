import asyncio
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("CAMPAIGN_STATE")

# 🔥 In-memory status tracker for campaigns
# { campaign_id: { "status": str, "task": asyncio.Task, "remaining": int, "total": int, "recipients": list } }
campaign_tracker: Dict[str, Any] = {}
