import threading
import requests
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class EngineKeepAlive:
    """
    Service to keep WhatsApp Engine alive by pinging it periodically
    Prevents Render cold starts by maintaining activity
    """
    
    def __init__(self, engine_url: str, ping_interval: int = 600):
        """
        Initialize keep-alive service
        
        Args:
            engine_url: WhatsApp Engine URL
            ping_interval: Time between pings in seconds (default: 600 = 10 minutes)
        """
        self.engine_url = engine_url.rstrip('/')
        self.ping_interval = ping_interval
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.last_ping_status: Optional[str] = None
        self.consecutive_failures = 0
        
    def start(self):
        """Start the keep-alive service in background thread"""
        if self.running:
            logger.warning("Keep-alive service is already running")
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._keep_alive_loop, daemon=True)
        self.thread.start()
        logger.info(f"Engine keep-alive service started for {self.engine_url}")
        
    def stop(self):
        """Stop the keep-alive service"""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
        logger.info("Engine keep-alive service stopped")
        
    def _keep_alive_loop(self):
        """Main loop that pings the engine periodically"""
        while self.running:
            try:
                self._ping_engine()
                self.consecutive_failures = 0
            except requests.exceptions.ConnectionError:
                self.consecutive_failures += 1
                # Log as warning since we handle it, but keep it visible
                logger.warning(f"Keep-alive connection refused (attempt {self.consecutive_failures})")
                
                # If too many consecutive failures, check if we're using localhost in a non-local environment
                if self.consecutive_failures >= 3:
                    if "localhost" in self.engine_url or "127.0.0.1" in self.engine_url:
                        logger.error("🛑 CRITICAL: Keep-alive is failing on localhost. If this is running on Render, "
                                     "you MUST set WHATSAPP_ENGINE_URL to the engine's public or internal Render URL.")
                    time.sleep(self.ping_interval * 2)
                    continue
            except Exception as e:
                self.consecutive_failures += 1
                logger.error(f"Keep-alive ping failed (attempt {self.consecutive_failures}): {e}")
                
                if self.consecutive_failures >= 3:
                    time.sleep(self.ping_interval * 2)
                    continue
                    
            time.sleep(self.ping_interval)
            
    def _ping_engine(self):
        """Ping the engine health endpoint"""
        health_url = f"{self.engine_url}/health"
        
        try:
            response = requests.get(
                health_url,
                timeout=15,  # Reduced from 30 to 15 for faster failure detection
                headers={'User-Agent': 'Keep-Alive-Service/1.0'}
            )
            
            if response.status_code == 200:
                self.last_ping_status = "success"
                logger.debug(f"Engine keep-alive ping successful: {response.status_code}")
            elif response.status_code == 404:
                self.last_ping_status = "waking_up"
                logger.info("Engine might be waking up (404 on health endpoint)")
            elif "text/html" in response.headers.get("Content-Type", ""):
                self.last_ping_status = "port_mismatch"
                logger.error(f"🚨 PORT MISMATCH: Engine {health_url} returned HTML instead of JSON. "
                             "Check if WHATSAPP_ENGINE_URL points to the correct service/port.")
            else:
                self.last_ping_status = f"error_{response.status_code}"
                logger.warning(f"Engine returned unexpected status: {response.status_code}")
                
        except requests.exceptions.Timeout:
            self.last_ping_status = "timeout"
            logger.warning(f"Engine keep-alive ping timed out for {health_url}")
            raise
        except requests.exceptions.ConnectionError:
            self.last_ping_status = "connection_error"
            # We don't log here, let the loop handle it
            raise
        except Exception as e:
            self.last_ping_status = "unknown_error"
            logger.error(f"Engine keep-alive ping failed: {e}")
            raise
            
    def get_status(self) -> dict:
        """Get current keep-alive service status"""
        return {
            "running": self.running,
            "engine_url": self.engine_url,
            "ping_interval": self.ping_interval,
            "last_ping_status": self.last_ping_status,
            "consecutive_failures": self.consecutive_failures
        }

# Global keep-alive instance
_keep_alive_service: Optional[EngineKeepAlive] = None

def initialize_keep_alive(engine_url: str, ping_interval: int = 600) -> EngineKeepAlive:
    """
    Initialize and start the global keep-alive service
    
    Args:
        engine_url: WhatsApp Engine URL
        ping_interval: Time between pings in seconds
        
    Returns:
        EngineKeepAlive instance
    """
    global _keep_alive_service
    
    if _keep_alive_service is None:
        _keep_alive_service = EngineKeepAlive(engine_url, ping_interval)
        _keep_alive_service.start()
        
    return _keep_alive_service

def get_keep_alive_service() -> Optional[EngineKeepAlive]:
    """Get the global keep-alive service instance"""
    return _keep_alive_service

def stop_keep_alive():
    """Stop the global keep-alive service"""
    global _keep_alive_service
    
    if _keep_alive_service:
        _keep_alive_service.stop()
        _keep_alive_service = None
