"""
Rate limiting configuration for WhatsApp Engine Service
"""
from datetime import timedelta
from typing import Dict, Any
import os

class RateLimitConfig:
    """Configuration for rate limiting and retry behavior"""
    
    # Environment detection
    PRODUCTION = os.getenv("ENVIRONMENT", "development").lower() == "production"
    
    # Retry configuration
    MAX_RETRIES = 5 if PRODUCTION else 7  # Reduced retries in production
    BASE_TIMEOUT = 90 if PRODUCTION else 60  # Longer timeout in production
    RETRY_DELAYS = [15, 30, 60, 120, 240] if PRODUCTION else [10, 20, 40, 80, 120, 180, 300]
    
    # Rate limiting configuration - more lenient in production
    RATE_LIMIT_WINDOW = timedelta(minutes=1)
    MAX_REQUESTS_PER_WINDOW = 100 if PRODUCTION else 20  # 🔥 FIX: Reduced dev limit from 30 to 20
    
    # QR-specific rate limiting
    QR_COOLDOWN_SECONDS = 3 if PRODUCTION else 8  # 🔥 FIX: Increased dev cooldown from 5 to 8
    
    # Status check cooldowns
    STATUS_CHECK_COOLDOWN_SECONDS = 5 if PRODUCTION else 10  # Shorter in production
    
    # Session start locks
    SESSION_START_LOCK_SECONDS = 45 if PRODUCTION else 30  # Longer lock in production
    
    # Default retry-after for 429 errors when not provided by server
    DEFAULT_RETRY_AFTER = 60 if PRODUCTION else 60  # 🔥 FIX: Increased dev default from 30 to 60
    
    # Circuit breaker configuration
    CIRCUIT_BREAKER_THRESHOLD = 10  # Number of failures before opening circuit
    CIRCUIT_BREAKER_TIMEOUT = 300  # 5 minutes before trying again
    CIRCUIT_BREAKER_HALF_OPEN_MAX_CALLS = 3  # Max calls in half-open state
    
    # Request deduplication
    DEDUPLICATION_WINDOW = timedelta(seconds=45)  # 🔥 FIX: Increased from 30s to 45s for better dedup
    
    @classmethod
    def get_config_dict(cls) -> Dict[str, Any]:
        """Get configuration as dictionary for logging/monitoring"""
        return {
            "environment": "production" if cls.PRODUCTION else "development",
            "max_retries": cls.MAX_RETRIES,
            "base_timeout": cls.BASE_TIMEOUT,
            "retry_delays": cls.RETRY_DELAYS,
            "rate_limit_window_minutes": cls.RATE_LIMIT_WINDOW.total_seconds() / 60,
            "max_requests_per_window": cls.MAX_REQUESTS_PER_WINDOW,
            "qr_cooldown_seconds": cls.QR_COOLDOWN_SECONDS,
            "status_check_cooldown_seconds": cls.STATUS_CHECK_COOLDOWN_SECONDS,
            "session_start_lock_seconds": cls.SESSION_START_LOCK_SECONDS,
            "default_retry_after": cls.DEFAULT_RETRY_AFTER,
            "circuit_breaker_threshold": cls.CIRCUIT_BREAKER_THRESHOLD,
            "circuit_breaker_timeout": cls.CIRCUIT_BREAKER_TIMEOUT,
            "deduplication_window_seconds": cls.DEDUPLICATION_WINDOW.total_seconds()
        }
