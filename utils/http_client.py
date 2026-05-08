import aiohttp
import asyncio
from typing import Dict, Any, Optional


class HTTPClient:
    """Async HTTP client for external API calls."""
    
    def __init__(self, base_url: str, headers: Optional[Dict[str, str]] = None):
        self.base_url = base_url
        self.headers = headers or {}
    
    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make GET request."""
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(f"{self.base_url}{endpoint}", params=params) as response:
                return await response.json()
    
    async def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make POST request."""
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.post(f"{self.base_url}{endpoint}", json=data) as response:
                return await response.json()
    
    async def put(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make PUT request."""
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.put(f"{self.base_url}{endpoint}", json=data) as response:
                return await response.json()
