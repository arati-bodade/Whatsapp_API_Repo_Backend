from fastapi import Request, HTTPException, status
from collections import defaultdict
import time
from typing import Dict, Tuple

class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # dict mapping ip to (count, window_start_time)
        self.requests: Dict[str, Tuple[int, float]] = defaultdict(lambda: (0, 0.0))

    def __call__(self, request: Request):
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        count, start_time = self.requests[client_ip]
        
        if current_time - start_time > self.window_seconds:
            # Reset window
            self.requests[client_ip] = (1, current_time)
        else:
            if count >= self.max_requests:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many requests. Please try again later."
                )
            self.requests[client_ip] = (count + 1, start_time)

# 5 attempts per minute
registration_rate_limiter = RateLimiter(max_requests=5, window_seconds=60)
