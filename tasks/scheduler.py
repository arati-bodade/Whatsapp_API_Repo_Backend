import asyncio
from typing import Callable, Any
from datetime import datetime, timedelta


class TaskScheduler:
    """Simple task scheduler for background jobs."""
    
    def __init__(self):
        self.tasks = []
        self.running = False
    
    def add_task(self, func: Callable, interval: int, *args, **kwargs):
        """Add a recurring task."""
        self.tasks.append({
            'func': func,
            'interval': interval,
            'args': args,
            'kwargs': kwargs,
            'last_run': None
        })
    
    async def start(self):
        """Start the scheduler."""
        self.running = True
        while self.running:
            current_time = datetime.now()
            
            for task in self.tasks:
                if (task['last_run'] is None or 
                    current_time - task['last_run'] >= timedelta(seconds=task['interval'])):
                    try:
                        await task['func'](*task['args'], **task['kwargs'])
                        task['last_run'] = current_time
                    except Exception as e:
                        print(f"Task error: {e}")
            
            await asyncio.sleep(1)
    
    def stop(self):
        """Stop the scheduler."""
        self.running = False


# Global scheduler instance
scheduler = TaskScheduler()
