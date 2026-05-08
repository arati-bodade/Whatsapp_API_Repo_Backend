import time
from fastapi import HTTPException, status, Request
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware."""
    
    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients = {}
    
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        current_time = time.time()
        
        # Clean old entries
        self.clients = {
            ip: times for ip, times in self.clients.items()
            if current_time - times[-1] < self.period
        }
        
        # Check rate limit
        if client_ip in self.clients:
            if len(self.clients[client_ip]) >= self.calls:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded"
                )
            self.clients[client_ip].append(current_time)
        else:
            self.clients[client_ip] = [current_time]
        
        response = await call_next(request)
        return response
