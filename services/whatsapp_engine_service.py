import requests
import logging
import time
import os
import uuid
import base64
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session
from models.device import Device, SessionStatus
from services.uuid_service import UUIDService
from services.session_validation_service import session_validation_service
from core.config import settings
from utils.phone_utils import normalize_phone
from services.message_usage_service import MessageUsageService
from rate_limit_config import RateLimitConfig
logger = logging.getLogger(__name__)

class WhatsAppEngineService:
    """Enhanced WhatsApp Engine service with retry logic, comprehensive logging, and fallback handling"""
    
    def __init__(self, db: Session = None):
        self.db = db
        self.engine_url = settings.WHATSAPP_ENGINE_BASE_URL
        self.message_usage_service = MessageUsageService(db) if db else None
        # 🔥 QR Cache: Store QR codes per device to prevent repeated engine calls
        self._qr_cache = {}  # {device_id: {"qr_code": str, "expires_at": datetime, "generated_at": datetime}}
        # 🔥 NEW: Request cooldowns to prevent rapid polling
        self._qr_request_cooldowns = {}  # {device_id: datetime}
        self._status_check_cooldowns = {}  # {device_id: datetime}
        # 🔥 CRITICAL: Session start locks to prevent duplicate start requests
        self._session_start_locks = {}  # {device_id: datetime} - tracks active session starts
        # 🔥 RATE LIMITING: Track request counts per device to prevent spam
        self._request_counters = {}  # {device_id: {"count": int, "window_start": datetime}}
        self._rate_limit_window = RateLimitConfig.RATE_LIMIT_WINDOW
        self._max_requests_per_window = RateLimitConfig.MAX_REQUESTS_PER_WINDOW
        self.max_retries = RateLimitConfig.MAX_RETRIES
        self.base_timeout = RateLimitConfig.BASE_TIMEOUT
        self.retry_delays = RateLimitConfig.RETRY_DELAYS
        
        # 🔥 CIRCUIT BREAKER: Prevent cascading failures
        self._circuit_breaker_state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self._circuit_breaker_failures = 0
        self._circuit_breaker_last_failure = None
        self._circuit_breaker_half_open_calls = 0
        
        # 🔥 REQUEST DEDUPLICATION: Prevent duplicate requests
        self._request_cache = {}  # {request_hash: {"timestamp": datetime, "result": Any}}
        
    def _check_circuit_breaker(self) -> bool:
        """Check if circuit breaker allows requests"""
        now = datetime.now(timezone.utc)
        
        if self._circuit_breaker_state == "OPEN":
            # Check if timeout has passed
            if (now - self._circuit_breaker_last_failure).total_seconds() > RateLimitConfig.CIRCUIT_BREAKER_TIMEOUT:
                self._circuit_breaker_state = "HALF_OPEN"
                self._circuit_breaker_half_open_calls = 0
                logger.info("🔄 Circuit breaker transitioning to HALF_OPEN")
                return True
            else:
                logger.warning("🚫 Circuit breaker OPEN - blocking requests")
                return False
        
        elif self._circuit_breaker_state == "HALF_OPEN":
            # Allow limited calls in half-open state
            if self._circuit_breaker_half_open_calls >= RateLimitConfig.CIRCUIT_BREAKER_HALF_OPEN_MAX_CALLS:
                logger.warning("🚫 Circuit breaker HALF_OPEN limit reached")
                return False
        
        return True
    
    def _record_circuit_breaker_success(self):
        """Record successful request for circuit breaker"""
        if self._circuit_breaker_state == "HALF_OPEN":
            self._circuit_breaker_half_open_calls += 1
            # If we've had enough successes, close the circuit
            if self._circuit_breaker_half_open_calls >= RateLimitConfig.CIRCUIT_BREAKER_HALF_OPEN_MAX_CALLS:
                self._circuit_breaker_state = "CLOSED"
                self._circuit_breaker_failures = 0
                logger.info("✅ Circuit breaker CLOSED - service recovered")
        elif self._circuit_breaker_state == "CLOSED":
            # Reset failure count on success
            self._circuit_breaker_failures = 0
    
    def _record_circuit_breaker_failure(self):
        """Record failed request for circuit breaker"""
        self._circuit_breaker_failures += 1
        self._circuit_breaker_last_failure = datetime.now(timezone.utc)
        
        if self._circuit_breaker_state == "CLOSED":
            if self._circuit_breaker_failures >= RateLimitConfig.CIRCUIT_BREAKER_THRESHOLD:
                self._circuit_breaker_state = "OPEN"
                logger.error(f"🚨 Circuit breaker OPEN after {self._circuit_breaker_failures} failures")
        elif self._circuit_breaker_state == "HALF_OPEN":
            # Any failure in half-open state immediately opens the circuit
            self._circuit_breaker_state = "OPEN"
            logger.error(f"🚨 Circuit breaker OPEN again after failure in HALF_OPEN state")
    
    def _get_request_hash(self, method: str, endpoint: str, **kwargs) -> str:
        """Generate hash for request deduplication"""
        import hashlib
        import json
        
        # Include custom headers in the hash to distinguish between different recipients/options
        # This is critical for file uploads where 'to' is in headers
        headers = kwargs.get("headers", {})
        wa_headers = {k: v for k, v in headers.items() if k.lower().startswith("x-wa-")}
        
        # Create a deterministic representation of the request
        request_data = {
            "method": method.upper(),
            "endpoint": endpoint,
            "json": kwargs.get("json", {}),
            "params": kwargs.get("params", {}),
            "headers": wa_headers
        }
        
        request_str = json.dumps(request_data, sort_keys=True)
        return hashlib.md5(request_str.encode()).hexdigest()
    
    def _check_duplicate_request(self, request_hash: str) -> Optional[Any]:
        """Check if request is a duplicate and return cached result if available"""
        now = datetime.now(timezone.utc)
        
        if request_hash in self._request_cache:
            cached = self._request_cache[request_hash]
            if (now - cached["timestamp"]).total_seconds() < RateLimitConfig.DEDUPLICATION_WINDOW.total_seconds():
                logger.debug(f"🔄 Returning cached result for duplicate request: {request_hash[:8]}...")
                return cached["result"]
            else:
                # Expired cache entry
                del self._request_cache[request_hash]
        
        return None
    
    def _cache_request_result(self, request_hash: str, result: Any):
        """Cache request result for deduplication"""
        self._request_cache[request_hash] = {
            "timestamp": datetime.now(timezone.utc),
            "result": result
        }
        
        # Cleanup old entries periodically
        if len(self._request_cache) > 1000:  # Prevent memory bloat
            self._cleanup_request_cache()
    
    def _cleanup_request_cache(self):
        """Clean up expired request cache entries"""
        now = datetime.now(timezone.utc)
        expired_keys = []
        
        for key, cached in self._request_cache.items():
            if (now - cached["timestamp"]).total_seconds() > RateLimitConfig.DEDUPLICATION_WINDOW.total_seconds():
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._request_cache[key]
        
        if expired_keys:
            logger.debug(f"🧹 Cleaned up {len(expired_keys)} expired cache entries")
    
    def _check_rate_limit(self, device_id: str) -> bool:
        """Check if device has exceeded rate limit"""
        now = datetime.now(timezone.utc)
        
        if device_id not in self._request_counters:
            self._request_counters[device_id] = {"count": 0, "window_start": now}
        
        counter = self._request_counters[device_id]
        
        # Reset window if expired
        if now - counter["window_start"] > self._rate_limit_window:
            counter["count"] = 0
            counter["window_start"] = now
        
        # Check if rate limit exceeded
        if counter["count"] >= self._max_requests_per_window:
            time_until_reset = self._rate_limit_window - (now - counter["window_start"])
            logger.warning(f"Rate limit exceeded for device {device_id}: {counter['count']}/{self._max_requests_per_window}. Reset in {time_until_reset.seconds}s")
            return False
        
        # Increment counter
        counter["count"] += 1
        logger.debug(f"Request count for device {device_id}: {counter['count']}/{self._max_requests_per_window}")
        return True
    
    def _get_cached_qr(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get cached QR code if still valid"""
        if device_id not in self._qr_cache:
            return None
            
        cached_data = self._qr_cache[device_id]
        now = datetime.now(timezone.utc)
        
        expires_at = cached_data["expires_at"]
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        
        # Check if QR is still valid (30-60 seconds)
        if now < expires_at:
            logger.info(f"🔄 Returning cached QR for device {device_id} (valid for {(expires_at - now).seconds}s)")
            return {
                "qr_code": cached_data["qr_code"],
                "status": "qr_ready",
                "cached": True,
                "expires_at": expires_at.isoformat()
            }
        else:
            # Remove expired cache
            del self._qr_cache[device_id]
            logger.info(f"🗑️ QR cache expired for device {device_id}")
            return None
    
    def _cache_qr(self, device_id: str, qr_code: str, expires_in_seconds: int = 45):
        """Cache QR code for device"""
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=expires_in_seconds)
        
        self._qr_cache[device_id] = {
            "qr_code": qr_code,
            "generated_at": now,
            "expires_at": expires_at
        }
        logger.info(f"💾 Cached QR for device {device_id} (expires in {expires_in_seconds}s)")
        
    def _make_request_with_retry(self, method: str, endpoint: str, **kwargs) -> Optional[requests.Response]:
        """Make HTTP request with retry logic, circuit breaker, and deduplication"""
        url = f"{self.engine_url}{endpoint}"
        
        # 🔥 CIRCUIT BREAKER: Check if requests are allowed
        if not self._check_circuit_breaker():
            logger.warning(f"Circuit breaker OPEN - blocking request to {endpoint}")
            mock_response = requests.Response()
            mock_response.status_code = 503
            mock_response.headers = {"Retry-After": str(RateLimitConfig.CIRCUIT_BREAKER_TIMEOUT)}
            return mock_response
        
        # 🔥 REQUEST DEDUPLICATION: Check for duplicate requests
        request_hash = self._get_request_hash(method, endpoint, **kwargs)
        cached_result = self._check_duplicate_request(request_hash)
        if cached_result is not None:
            return cached_result
        
        # Extract device_id from endpoint for rate limiting
        device_id = None
        if "/session/" in endpoint:
            parts = endpoint.split("/session/")
            if len(parts) > 1:
                device_id = parts[1].split("/")[0]
        
        # Check rate limiting if device_id is available
        if device_id and not self._check_rate_limit(device_id):
            # Return a mock 429 response to trigger rate limiting handling
            logger.warning(f"Rate limit exceeded for device {device_id}, blocking request")
            mock_response = requests.Response()
            mock_response.status_code = 429
            mock_response.headers = {"Retry-After": "60"}
            return mock_response
        
        # Use longer timeout for message sends
        is_message_send = "/message" in endpoint
        timeout = kwargs.pop('timeout', self.base_timeout + (20 if is_message_send else 0))
        
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Engine request - Attempt {attempt + 1}/{self.max_retries}: {method.upper()} {url}")
                if is_message_send:
                    logger.debug(f"   Using extended timeout for message send: {timeout}s")
                
                response = requests.request(
                    method=method,
                    url=url,
                    timeout=timeout,
                    **kwargs
                )
                
                # 🔥 VALIDATION: Check if response is JSON (engine) or HTML (Render wake-up / Frontend)
                content_type = response.headers.get('content-type', '').lower()
                if 'text/html' in content_type:
                    # If on Render, this often means the cold-start loading page
                    logger.warning(f"⚠️ [RENDER_COLD_START] Engine URL {url} returned HTML. This usually means the Render service is waking up.")
                    logger.warning(f"⚠️ Retrying (Attempt {attempt + 1}/{self.max_retries}). Please wait roughly 60 seconds.")
                    
                    # Render take ~30-60s to boot. If we hit HTML, we should wait longer.
                    wait_time = max(30, self.retry_delays[attempt])
                    time.sleep(wait_time)
                    continue
                elif response.status_code in [200, 202]:
                    # 🔥 CIRCUIT BREAKER: Record success
                    self._record_circuit_breaker_success()
                    
                    # 🔥 REQUEST DEDUPLICATION: Cache successful result
                    self._cache_request_result(request_hash, response)
                    
                    return response
                elif response.status_code == 429:  # Rate limit - retry with exponential backoff
                    to_info = kwargs.get('json', {}).get('to', 'N/A')
                    retry_after = response.headers.get('Retry-After', RateLimitConfig.DEFAULT_RETRY_AFTER)
                    try:
                        retry_after = int(retry_after)
                    except (ValueError, TypeError):
                        retry_after = 30
                    
                    # Use exponential backoff with minimum of Retry-After header
                    backoff_delay = max(retry_after, self.retry_delays[min(attempt, len(self.retry_delays) - 1)])
                    logger.warning(f"Rate limited (Recipient: {to_info}) - Status: 429, Retry-After: {retry_after}s, Using backoff: {backoff_delay}s")
                    
                    if attempt < self.max_retries - 1:
                        time.sleep(backoff_delay)
                    continue
                elif response.status_code in [404, 400, 409, 422]:  # Client errors, don't retry
                    logger.warning(f"Engine client error - Status: {response.status_code}")
                    return response
                else:  # Server errors, retry
                    to_info = kwargs.get('json', {}).get('to', 'N/A')
                    logger.warning(f"Engine server error (Recipient: {to_info}) - Status: {response.status_code}, Will retry")
                    
                    # 🔥 CIRCUIT BREAKER: Record failure for server errors
                    self._record_circuit_breaker_failure()
                    
            except requests.exceptions.ConnectionError as e:
                logger.warning(f"Engine connection error - Attempt {attempt + 1}: {str(e)}")
                # 🔥 CIRCUIT BREAKER: Record connection failures
                self._record_circuit_breaker_failure()
                
                if attempt == self.max_retries - 1:
                     logger.error(f"❌ Engine Unreachable at {self.engine_url}")
                     raise ConnectionError(f"ENGINE_DOWN: Could not connect to WhatsApp Engine at {self.engine_url}")
            except Exception as e:
                logger.error(f"Engine request error - Attempt {attempt + 1}: {str(e)}")
                # 🔥 CIRCUIT BREAKER: Record general failures
                self._record_circuit_breaker_failure()
                
                if "PORT_MISMATCH" in str(e):
                    raise e
            
            if attempt < self.max_retries - 1:
                time.sleep(self.retry_delays[attempt])
        
        # 🔥 CIRCUIT BREAKER: Record final failure if all retries exhausted
        self._record_circuit_breaker_failure()
        return None
    
    def get_production_metrics(self) -> Dict[str, Any]:
        """Get production metrics for monitoring"""
        return {
            "circuit_breaker": {
                "state": self._circuit_breaker_state,
                "failures": self._circuit_breaker_failures,
                "last_failure": self._circuit_breaker_last_failure.isoformat() if self._circuit_breaker_last_failure else None,
                "half_open_calls": self._circuit_breaker_half_open_calls
            },
            "rate_limiting": {
                "active_devices": len(self._request_counters),
                "cached_requests": len(self._request_cache),
                "qr_cache_size": len(self._qr_cache),
                "rate_limit_config": RateLimitConfig.get_config_dict()
            },
            "environment": {
                "production": RateLimitConfig.PRODUCTION,
                "engine_url": self.engine_url
            }
        }
    
    def _make_request_with_timeout(self, method: str, endpoint: str, timeout: int = 5, **kwargs) -> Optional[requests.Response]:
        """Make a single request with specific timeout (no retries)"""
        try:
            url = f"{self.engine_url}{endpoint}"
            logger.debug(f"Making single request to {url} with timeout {timeout}s")
            
            response = requests.request(
                method=method,
                url=url,
                timeout=timeout,
                **kwargs
            )
            
            logger.debug(f"Single request response - Status: {response.status_code}")
            return response
            
        except requests.exceptions.Timeout as e:
            logger.error(f"❌ [ENGINE_TIMEOUT] Request to {url} ({endpoint}) timed out after {timeout}s: {str(e)}")
            return None
        except requests.exceptions.ConnectionError as e:
            logger.error(f"❌ [ENGINE_CONNECTION_ERROR] Could not connect to {url}: {str(e)}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ [ENGINE_REQUEST_EXCEPTION] Error during request to {url} ({endpoint}): {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"❌ [ENGINE_RESPONSE_DEBUG] Status: {e.response.status_code}, Body: {e.response.text[:200]}")
            return None
        except Exception as e:
            logger.error(f"❌ [ENGINE_UNEXPECTED_ERROR] {url}: {str(e)}")
            return None

    def _handle_response_errors(self, response: requests.Response, endpoint_name: str) -> Dict[str, Any]:
        """Centralized helper to handle non-2xx engine responses"""
        # Status code check
        if response.status_code == 502:
            err_msg = "Engine is temporarily unavailable (Bad Gateway 502). Please retry in 1 minute as it may be restarting."
        elif response.status_code == 503:
            err_msg = "Engine is currently overloaded or restarting (Service Unavailable 503). Please retry in a moment."
        elif response.status_code == 504:
            err_msg = "Engine took too long to respond (Gateway Timeout 504). The message might still be sent in the background."
            err_code = "ENGINE_GATEWAY_TIMEOUT"
        elif "text/html" in response.headers.get("Content-Type", ""):
                err_msg = f"Engine returned HTML ({response.status_code}) - possible port/URL mismatch."
                err_code = "ENGINE_HTML_RESPONSE"
        else:
            try:
                err_body = response.json()
                err_msg = err_body.get('message', err_body.get('error', f'Engine error {response.status_code}'))
                err_code = err_body.get('error_code') or err_body.get('error')
                
                # If it's a specific interesting error, we can return it as the 'message' 
                # or attach it to the result
                if err_code:
                    logger.error(f"❌ [ENGINE_ERROR_CODE] {err_code}")
            except:
                err_msg = f"Engine error {response.status_code}"
                err_code = None

        logger.error(f"❌ [{endpoint_name}_ERROR] {err_msg}")
        return {"success": False, "message": err_msg, "error_code": err_code, "data": None}
    
    def check_message_status(self, device_id: str, message_id: str) -> Dict[str, Any]:
        """Check the status of an async message"""
        logger.info(f"Checking message status for {message_id} on device {device_id}")
        
        response = self._make_request_with_timeout("GET", f"/session/{device_id}/message/{message_id}/status", timeout=3)
        
        if response is None:
            error_msg = f"Failed to check message status: No response from engine (check connectivity/logs)"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
        
        if response.status_code == 200:
            try:
                result = response.json()
                logger.info(f"Message status retrieved: {result}")
                return {"success": True, "result": result}
            except Exception as e:
                logger.error(f"Failed to parse message status response: {str(e)}")
                return {"success": False, "error": f"Invalid response: {str(e)}"}
        
        error_msg = f"Failed to check message status: HTTP {response.status_code}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}
    
    def check_engine_reachable(self) -> bool:
        """Check if WhatsApp Engine socket is reachable (lightweight connectivity check)"""
        try:
            response = requests.get(f"{self.engine_url}/", timeout=2)
            logger.debug(f"Engine socket reachable (HTTP {response.status_code})")
            return True
        except requests.exceptions.ConnectionError as e:
            logger.debug(f"Engine socket unreachable: {str(e)}")
            return False
        except Exception as e:
            logger.debug(f"Engine socket check error: {str(e)}")
            return False
    
    def _is_qr_request_allowed(self, device_id: str) -> bool:
        """Check if QR request is allowed (cooldown mechanism)"""
        now = datetime.now(timezone.utc)
        last_request = self._qr_request_cooldowns.get(device_id)
        
        if last_request:
            time_since_last = now - last_request
            # 🔥 FIXED: Use configured cooldown between QR requests to prevent spam
            if time_since_last < timedelta(seconds=RateLimitConfig.QR_COOLDOWN_SECONDS):
                logger.debug(f"⏸️ QR request cooldown for {device_id}: {time_since_last.seconds}s since last request")
                return False
        
        return True
    
    def _record_qr_request(self, device_id: str):
        """Record that a QR request was performed"""
        self._qr_request_cooldowns[device_id] = datetime.now(timezone.utc)
        logger.debug(f"📝 QR request recorded for {device_id}")
    
    def get_qr_code(self, device_id: str) -> Dict[str, Any]:
        """Get QR code for device with caching to prevent repeated engine calls"""
        logger.info(f"Getting QR code for device {device_id}")
        
        # 🔥 STEP 1: Check cache first to prevent repeated engine calls
        cached_qr = self._get_cached_qr(device_id)
        if cached_qr:
            return {"success": True, "data": cached_qr}
        
        # 🔥 STEP 2: NEW - Apply cooldown to prevent rapid QR requests
        if not self._is_qr_request_allowed(device_id):
            return {
                "success": False,
                "error": "QR_REQUEST_COOLDOWN",
                "message": "Please wait a few seconds before requesting QR code again"
            }
        
        # 🔥 STEP 3: Generate new QR (only when cache is empty and no cooldown)
        response = self._make_request_with_retry("GET", f"/session/{device_id}/qr", timeout=10)
        
        if response is not None:
            # 🔥 CRITICAL: Validate response is JSON, not HTML
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' in content_type:
                logger.error(f"🚨 ENGINE MISCONFIG: Engine returned HTML instead of JSON!")
                logger.error(f"🚨 This means backend is hitting frontend, not engine!")
                logger.error(f"🚨 Content-Type: {content_type}")
                logger.error(f"🚨 Response preview: {response.text[:200]}...")
                return {
                    "success": False, 
                    "error": "ENGINE_NOT_READY",
                    "details": "Engine returned HTML instead of JSON - check engine port configuration"
                }
            
            if response.status_code == 200:
                try:
                    qr_data = response.json()
                    qr_code = qr_data.get('qr_code') or qr_data.get('qr')
                    
                    if qr_code:
                        # Cache the QR for 45 seconds
                        self._cache_qr(device_id, qr_code, expires_in_seconds=45)
                        # Record successful QR generation
                        session_validation_service.record_qr_generation(device_id)
                        # Record QR request for cooldown
                        self._record_qr_request(device_id)
                        
                        return {
                            "success": True, 
                            "data": {
                                **qr_data,
                                "cached": False,
                                "expires_at": (datetime.now(timezone.utc) + timedelta(seconds=45)).isoformat()
                            }
                        }
                    # 🔥 FIXED: Handle connected state without QR
                    elif qr_data.get("status") == "connected":
                        return {
                            "success": True,
                            "data": {"status": "connected"}
                        }
                    else:
                        logger.error(f"Engine response missing QR code: {qr_data}")
                        return {"success": False, "error": "Invalid QR response from engine"}
                        
                except Exception as e:
                    logger.error(f"Failed to parse QR JSON response: {e}")
                    return {"success": False, "error": f"Invalid JSON: {str(e)}"}
                    
            elif response.status_code == 202:
                # QR still generating - don't cache yet
                return {"success": True, "data": {"status": "pending", "qr": None}}
                
            elif response.status_code == 404:
                return {"success": False, "error": "Device session not found"}
            else:
                logger.error(f"Unexpected QR response status: {response.status_code}")
                return {"success": False, "error": f"Engine returned status {response.status_code}"}
        
        return {"success": False, "error": "Failed to get QR code"}

    def check_engine_health(self) -> Dict[str, Any]:
        """Check if WhatsApp Engine is healthy (comprehensive health check)"""
        response = self._make_request_with_retry("GET", "/health")
        
        if response and response.status_code == 200:
            try:
                health_data = response.json()
                logger.info(f"Engine health check successful: {health_data}")
                return {
                    "healthy": True,
                    "data": health_data
                }
            except Exception as e:
                logger.error(f"Failed to parse engine health response: {str(e)}")
                return {"healthy": False, "error": "Invalid response format"}
        
        error_msg = f"Engine health check failed" + (f": HTTP {response.status_code}" if response else ": No response")
        logger.error(error_msg)
        return {"healthy": False, "error": error_msg}
    
    def check_device_status(self, device_id: str) -> Dict[str, Any]:
        """Check device status in WhatsApp Engine with validation"""
        logger.info(f"Checking device status for {device_id}")
        
        # First check if engine is reachable
        if not self.check_engine_reachable():
            logger.warning(f"Engine unreachable, cannot check device {device_id}")
            return {"status": "engine_unreachable", "error": "WhatsApp Engine is not reachable"}
        
        response = self._make_request_with_retry("GET", f"/session/{device_id}/status")
        
        if response is not None:
            if response.status_code == 200:
                try:
                    data = response.json()
                    logger.info(f"Device {device_id} status: {data.get('status')}")
                    return {"status": data.get('status'), "engine_response": data}
                except Exception as e:
                    logger.error(f"Failed to parse device status response for {device_id}: {str(e)}")
                    return {"status": "parse_error", "error": str(e)}
            elif response.status_code == 404:
                logger.info(f"Device {device_id} not found in engine")
                return {"status": "not_found", "error": "Device not found in WhatsApp Engine"}
            else:
                logger.warning(f"Unexpected status checking device {device_id}: {response.status_code}")
                return {"status": "error", "error": f"HTTP {response.status_code}"}
        
        return {"status": "engine_unreachable", "error": "Failed to connect to WhatsApp Engine"}
    
    def sync_device_status(self, device_id: str) -> bool:
        """Sync device status with WhatsApp Engine and update database"""
        logger.info(f"Syncing device status for {device_id}")
        
        device_status = self.check_device_status(device_id)
        engine_status = device_status.get("status")
        
        if engine_status == "engine_unreachable":
            logger.warning(f"Engine unreachable, marking device {device_id} as offline")
            self._mark_device_offline(device_id, "Engine unreachable")
            return False
        
        # ✅ Convert string UUID to UUID object before query
        device_uuid = UUIDService.safe_convert(device_id)
        device = self.db.query(Device).filter(Device.device_id == device_uuid).first()
        if not device:
            logger.error(f"Device {device_id} not found in database")
            return False
        
        # Map engine status to database status
        if engine_status == "connected":
            new_status = SessionStatus.connected
            logger.info(f"Device {device_id} is connected in engine")
        elif engine_status == "qr_ready":
            new_status = SessionStatus.qr_ready
            logger.info(f"Device {device_id} has QR ready")
        elif engine_status == "connecting":
            new_status = SessionStatus.connecting
            logger.info(f"Device {device_id} is connecting")
        else:  # not_found, error, etc.
            new_status = SessionStatus.disconnected
            logger.info(f"Device {device_id} is not connected (status: {engine_status})")
            
            # 🔥 AUTO-HEAL: If session is missing in engine but was connected in DB, try starting it
            if engine_status == "not_found" and device.session_status == SessionStatus.connected:
                logger.warning(f"👻 Ghost session detected for {device_id} (missing in engine). Attempting to auto-start...")
                self.start_session(device_id)
                # We return False for now because starting session takes time,
                # but the next sync attempt might see it as 'connecting' or 'connected'
        
        # Update device status if changed
        if device.session_status != new_status:
            old_status = device.session_status
            device.session_status = new_status
            device.last_active = datetime.now(timezone.utc)
            self.db.commit()
            logger.info(f"Device {device_id} status updated: {old_status} -> {new_status}")
        
        return engine_status == "connected"
    
    def send_message(self, device_id: str, to: str, message: str, skip_credit_deduction: bool = False, authenticated_user_id: Optional[str] = None) -> Dict[str, Any]:
        """Send message with comprehensive validation and error handling"""
        # Alias for backward compatibility if skip_report was used elsewhere
        skip_report = skip_credit_deduction
        logger.info(f"Attempting to send message from device {device_id} to {to} (skip_report={skip_report})")
        
        # Check engine health first
        engine_health = self.check_engine_health()
        if not engine_health["healthy"]:
            error_msg = f"Cannot send message - Engine unhealthy: {engine_health.get('error', 'Unknown error')}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
        
        # 🔥 FETCH DEVICE FROM DB TO GET USER_ID
        device = self._validate_device_for_api(device_id)
        
        # Check device status
        device_status = self.check_device_status(device_id)
        if device_status.get("status") != "connected":
            error_msg = f"Cannot send message - Device not connected: {device_status.get('error', device_status.get('status'))}"
            logger.error(error_msg)
            # Mark device as offline in database
            self._mark_device_offline(device_id, f"Device not connected: {device_status.get('status')}")
            return {"success": False, "error": error_msg}
        
        # Normalize 'to' address (auto-add country code if needed)
        normalized_to = normalize_phone(to)
        if not normalized_to:
            return {"success": False, "error": f"Invalid recipient number: {to}"}
        
        # Send message - Engine now responds immediately with async acceptance
        payload = {"to": normalized_to, "message": message}
        logger.info(f"   Payload: {payload}")
        
        # Use reasonable timeout for acceptance (Engine responds immediately now, but increased just in case)
        response = self._make_request_with_timeout("POST", f"/session/{device_id}/message", json=payload, timeout=20)
        
        if response is not None and response.status_code == 200:
            try:
                result = response.json()
                logger.info(f"Message accepted by engine from device {device_id}: {result}")
                
                # Handle both old sync response and new async response
                if result.get("status") in ["accepted", "sent"]:
                    message_id = result.get("messageId") or f"msg-{uuid.uuid4().hex[:8]}"

                    if not skip_report and device:
                        # 🔥 LOG TO DELIVERY REPORTS
                        self._log_message(
                            db=self.db,
                            user_id=authenticated_user_id or device.busi_user_id,
                            device_id=device_id,
                            to=normalized_to,
                            message=message,
                            msg_type="TEXT",
                            status="SENT"
                        )
                        
                        # 🔥 HANDLE CREDITS (Using MessageUsageService if DB available)
                        if self.message_usage_service and not skip_credit_deduction:
                            try:
                                self.message_usage_service.deduct_credits(str(authenticated_user_id or device.busi_user_id), message_id)
                            except Exception as cred_err:
                                logger.error(f"⚠️ Credit deduction failed in send_message: {cred_err}")
                        
                        self.db.commit()

                    return {
                        "success": True, 
                        "result": result,
                        "async": result.get("status") == "accepted",
                        "messageId": message_id,
                        "note": result.get("note", "Message processed")
                    }
                else:
                    # Unexpected response format
                    logger.warning(f"Unexpected response format: {result}")
                    return {"success": True, "result": result}
                    
            except Exception as e:
                logger.error(f"Failed to parse send message response: {str(e)}")
                return {"success": False, "error": f"Invalid response: {str(e)}"}
        
        error_msg = f"Failed to send message" + (f": HTTP {response.status_code}" if response else ": No response")
        logger.error(error_msg)
        
        # 🔥 AUTO-HEALING: Check for Ghost Connection (DB says connected, Engine says 400 not connected)
        if response is not None and response.status_code == 400:
            try:
                error_data = response.json()
                if error_data.get("error") == "device_not_connected" or "not connected" in error_data.get("message", "").lower():
                    logger.warning(f"👻 Ghost connection detected for {device_id} during send. Auto-healing...")
                    self._mark_device_offline(device_id, "Auto-Heal: Engine reported not connected during send")
                    return {
                        "success": False, 
                        "error": "Device connection was lost. Please reconnect the device."
                    }
            except Exception as e:
                logger.error(f"Failed to parse error response for auto-healing: {e}")
            
            # Fallback sync if other 400 error
            self.sync_device_status(device_id)
        
        return {"success": False, "error": error_msg}
    
    def reconnect_device(self, device_id: str) -> Dict[str, Any]:
        """Attempt to reconnect a device"""
        logger.info(f"Attempting to reconnect device {device_id}")
        
        response = self._make_request_with_retry("POST", f"/session/{device_id}/reconnect")
        
        if response is not None and response.status_code == 200:
            try:
                result = response.json()
                logger.info(f"Reconnect initiated for device {device_id}: {result}")
                return {"success": True, "result": result}
            except Exception as e:
                logger.error(f"Failed to parse reconnect response: {str(e)}")
                return {"success": False, "error": f"Invalid response: {str(e)}"}
        
        error_msg = f"Failed to reconnect device" + (f": HTTP {response.status_code}" if response else ": No response")
        logger.error(error_msg)
        return {"success": False, "error": error_msg}
    
    def start_session(self, device_id: str) -> Dict[str, Any]:
        """Manually start/initialize a session with health check and duplicate prevention"""
        logger.info(f"Attempting to start session for device {device_id}")
        
        # CRITICAL: Check for duplicate start request (lock mechanism)
        now = datetime.now(timezone.utc)
        if device_id in self._session_start_locks:
            last_start = self._session_start_locks[device_id]
            time_since_last = now - last_start
            # If another start was requested within configured lock duration, ignore it
            if time_since_last < timedelta(seconds=RateLimitConfig.SESSION_START_LOCK_SECONDS):
                logger.warning(f"Duplicate start request blocked for {device_id} (last start {time_since_last.seconds}s ago)")
                return {"success": False, "error": "SESSION_START_IN_PROGRESS", "message": "Session start already in progress, please wait"}
        
        # STEP 1: Check engine health before attempting start
        engine_health = self.check_engine_health()
        if not engine_health["healthy"]:
            error_msg = f"Engine unhealthy, cannot start session: {engine_health.get('error', 'Unknown error')}"
            logger.error(error_msg)
            # CRITICAL: Do NOT mark device as disconnected if engine is unreachable
            # This prevents false disconnects during engine restarts
            return {"success": False, "error": "ENGINE_UNHEALTHY", "message": error_msg}
        
        # STEP 2: Set lock to prevent duplicate starts
        self._session_start_locks[device_id] = now
        logger.info(f"Session start lock acquired for {device_id}")
        
        try:
            # STEP 3: Attempt session start with retry
            response = self._make_request_with_retry("POST", f"/session/{device_id}/start")
            
            if response is not None and response.status_code == 200:
                try:
                    result = response.json()
                    logger.info(f"Session start initiated for device {device_id}: {result}")
                    return {"success": True, "result": result}
                except Exception as e:
                    logger.error(f"Failed to parse start session response: {str(e)}")
                    return {"success": False, "error": f"Invalid response: {str(e)}"}
            
            error_msg = f"Failed to start session" + (f": HTTP {response.status_code}" if response else ": No response")
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
        finally:
            # STEP 4: Release lock after 30 seconds (allow retry if failed)
            def release_lock():
                if device_id in self._session_start_locks:
                    del self._session_start_locks[device_id]
                    logger.info(f"Session start lock released for {device_id}")
            
            import threading
            timer = threading.Timer(float(RateLimitConfig.SESSION_START_LOCK_SECONDS), release_lock)
            timer.start()
    
    def _mark_device_offline(self, device_id: str, reason: str):
        """Mark device as offline in database with reason"""
        try:
            # Convert string UUID to UUID object before query
            device_uuid = UUIDService.safe_convert(device_id)
            device = self.db.query(Device).filter(Device.device_id == device_uuid).first()
            if device:
                old_status = device.session_status
                device.session_status = SessionStatus.disconnected
                device.last_active = datetime.now(timezone.utc)
                self.db.commit()
                logger.info(f"Device {device_id} marked offline: {old_status} -> disconnected. Reason: {reason}")
            else:
                logger.error(f"Device {device_id} not found in database when trying to mark offline")
        except Exception as e:
            logger.error(f"Failed to mark device {device_id} offline: {str(e)}")
    
    def get_all_sessions(self) -> Dict[str, Any]:
        """Get all sessions from engine"""
        response = self._make_request_with_retry("GET", "/sessions")
        
        if response is not None and response.status_code == 200:
            try:
                sessions = response.json()
                logger.info(f"Retrieved {len(sessions)} sessions from engine")
                return {"success": True, "sessions": sessions}
            except Exception as e:
                logger.error(f"Failed to parse sessions response: {str(e)}")
                return {"success": False, "error": str(e)}
        
        error_msg = f"Failed to get sessions" + (f": HTTP {response.status_code}" if response else ": No response")
        logger.error(error_msg)
        return {"success": False, "error": error_msg}
    
    def delete_session(self, device_id: str) -> Dict[str, Any]:
        """Delete a session from engine"""
        logger.info(f"Attempting to delete session for device {device_id}")
        
        response = self._make_request_with_retry("DELETE", f"/session/{device_id}")
        
        if response is not None and response.status_code == 200:
            try:
                result = response.json()
                logger.info(f"Session deleted successfully for device {device_id}: {result}")
                return {"success": True, "result": result}
            except Exception as e:
                logger.error(f"Failed to parse delete session response: {str(e)}")
                return {"success": False, "error": f"Invalid response: {str(e)}"}
        elif response is not None and response.status_code == 404:
            # Session doesn't exist in engine - that's ok for deletion
            logger.info(f"Session {device_id} not found in engine (404), treating as deleted")
            return {"success": True, "result": {"status": "not_found", "message": "Session not found in engine"}}
        
        error_msg = f"Failed to delete session" + (f": HTTP {response.status_code}" if response else ": No response")
        logger.error(error_msg)
        return {"success": False, "error": error_msg}

    def _validate_device_for_api(self, device_id: str) -> Device:
        device = None
        if self.db is not None:
            device_uuid = UUIDService.safe_convert(device_id)
            device = self.db.query(Device).filter(Device.device_id == device_uuid).first()
            if not device:
                raise HTTPException(status_code=404, detail="Device not found")
        
        if not self.check_engine_reachable():
            raise HTTPException(status_code=503, detail="WhatsApp Engine is unavailable")
        
        return device

    def send_text(self, device_id: str, to: str, message: str, device_name: str, skip_credit_deduction: bool = False, authenticated_user_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Send a plain text message via WhatsApp engine"""
        logger.info(f"🚀 [SEND_TEXT] To: {to}, Device: {device_id}")
        try:
            device = self._validate_device_for_api(device_id)
            normalized_to = normalize_phone(to)
            if not normalized_to:
                return {"success": False, "error": f"Invalid recipient number: {to}"}
                
            payload = {"to": normalized_to, "message": message, "wait": kwargs.get('wait_for_delivery', False)}
            response = self._make_request_with_retry("POST", f"/session/{device_id}/message", json=payload, timeout=kwargs.get('max_wait_time', 60) + 5)
            
            if response is None:
                logger.error(f"❌ [SEND_TEXT] Engine unresponsive after retries for {device_id}")
                return {"success": False, "message": "WhatsApp Engine is not responding. Please try again after 1 minute as it may be restarting.", "data": None}
                
            logger.info(f"🚀 [SEND_TEXT] Status: {response.status_code}")

            # Handle socket_not_ready (zombie session) – prompt user to reconnect
            if response.status_code == 503:
                try:
                    err_data = response.json()
                    err_code = err_data.get('error', '')
                    if err_code == 'socket_not_ready':
                        logger.error(f"❌ [SEND_TEXT] Device {device_id} has zombie socket - needs reconnect")
                        return {
                            "success": False,
                            "message": "WhatsApp connection lost. Please go to Devices page and reconnect by scanning the QR code.",
                            "error": "socket_not_ready",
                            "data": None
                        }
                except:
                    pass
                return {"success": False, "message": f"Engine unavailable (503). Try again in a few seconds.", "data": None}

            if response is not None and response.status_code in [200, 201, 202]:
                result_data = response.json()
                message_id = result_data.get('messageId') or f"engine-{uuid.uuid4().hex[:8]}"
                
                if self.message_usage_service and device and not skip_credit_deduction:
                    try:
                        self.message_usage_service.deduct_credits(str(authenticated_user_id or device.busi_user_id), message_id)
                        # 🔥 LOG TO DELIVERY REPORTS
                        self._log_message(
                            db=self.db,
                            user_id=authenticated_user_id or device.busi_user_id,
                            device_id=device_id,
                            to=normalized_to,
                            message=message,
                            msg_type="TEXT",
                            status="SENT"
                        )
                        self.db.commit()
                    except Exception as credit_err:
                        logger.error(f"⚠️ Credit/Report logging failed: {str(credit_err)}")

                return {"success": True, "message": "Message sent successfully", "data": result_data}
            
            return self._handle_response_errors(response, "SEND_TEXT")
        except Exception as e:
            logger.exception(f"❌ [SEND_TEXT_EXCEPTION] {str(e)}")
            return {"success": False, "message": f"Service error: {str(e)}", "data": None}

    def _log_message(self, db: Session, user_id: Any, device_id: str, to: str, message: str, msg_type: str, status: str):
        """Standard login for all outgoing unofficial messages so they show in Reports"""
        try:
            from models.message import Message, MessageMode, MessageType, ChannelType, MessageStatus
            
            # 🔥 DYNAMIC RATE LOOKUP
            from services.message_usage_service import MessageUsageService
            usage_service = MessageUsageService(db)
            rate = usage_service.get_deduction_rate(str(user_id))

            # Create persistent log record
            db_message = Message(
                message_id=uuid.uuid4(),
                busi_user_id=user_id,
                channel=ChannelType.WHATSAPP,
                mode=MessageMode.UNOFFICIAL,
                sender_number=str(device_id),
                receiver_number=to,
                message_type=getattr(MessageType, msg_type, MessageType.TEXT),
                message_body=message[:1000], 
                status=getattr(MessageStatus, status, MessageStatus.SENT),
                credits_used=rate,
                sent_at=datetime.now(timezone.utc)
            )
            db.add(db_message)
        except Exception as e:
            logger.error(f"Failed to log message to report table: {str(e)}")

    def send_file(self, device_id: str, to: str, file_path: str, device_name: str, skip_credit_deduction: bool = False, authenticated_user_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Send a file (local path or URL) via WhatsApp engine"""
        logger.info(f"🚀 [SEND_FILE] To: {to}, Path: {file_path}")
        try:
            device = self._validate_device_for_api(device_id)
            normalized_to = normalize_phone(to)
            if not normalized_to:
                return {"success": False, "error": f"Invalid recipient number: {to}"}
            
            # Detect if file is local (starts with / or is a relative path that exist)
            is_local = not file_path.startswith('http') and (file_path.startswith('/') or os.path.exists(file_path))
            
            if is_local and os.path.exists(file_path):
                # 🔥 ROBUST FIX: Use multipart/form-data for local files instead of large Base64 strings
                # This prevents 'Response ended prematurely' errors for large videos
                try:
                    # 🔥 UUID STRIP FIX: Remove storage UUID prefix for clean recipient view
                    import re
                    import mimetypes
                    raw_filename = os.path.basename(file_path)
                    # Handle both formats: trigger_UUID.ext and trigger_UUID_name.ext
                    if re.match(r'^trigger_[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}_', raw_filename):
                        # Format: trigger_UUID_name.ext -> name.ext (remove only UUID)
                        filename = re.sub(r'^trigger_[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}_', '', raw_filename)
                    else:
                        # No trigger UUID prefix, use as-is
                        filename = raw_filename
                    
                    mime_type, _ = mimetypes.guess_type(file_path)
                    mime_type = mime_type or 'application/octet-stream'
                    
                    # Clean caption
                    user_caption = kwargs.get('caption')
                    if user_caption:
                        # Also clean the user caption if it contains the filename
                        user_caption = user_caption.replace(raw_filename, filename)
                    
                    final_caption = user_caption if user_caption is not None else ""
                    
                    payload = {
                        "to": normalized_to, 
                        "caption": final_caption
                    }
                    
                    # 🔥 ZERO-DEPENDENCY FIX: Send as raw binary body with metadata in headers
                    # This avoids needing 'multer' on the engine side
                    # Headers must be Latin-1/ASCII safe, so we sanitize them
                    import urllib.parse
                    def sanitize_header(val):
                        if not val: return ""
                        # 🔥 CRITICAL: Use URL encoding to support Marathi/Unicode in headers
                        # This avoids the 'Invalid header value' error while preserving characters
                        stripped = str(val).replace("\r", " ").replace("\n", " ").strip()
                        return urllib.parse.quote(stripped)

                    headers = {
                        "X-WA-To": sanitize_header(normalized_to),
                        "X-WA-Filename": sanitize_header(filename),
                        "X-WA-Caption": sanitize_header(final_caption),
                        "X-WA-MimeType": sanitize_header(mime_type),
                        "X-WA-Wait": "true" if kwargs.get('wait_for_delivery', False) else "false",
                        "Content-Type": "application/octet-stream"
                    }
                    
                    logger.info(f"📤 [SEND_FILE] Streaming raw binary: {filename} ({mime_type})")
                    
                    with open(file_path, "rb") as f:
                        response = self._make_request_with_retry(
                            "POST", 
                            f"/session/{device_id}/file", 
                            data=f, # Stream directly from disk
                            headers=headers,
                            timeout=kwargs.get('max_wait_time', 60) + 10
                        )
                except Exception as file_err:
                    logger.error(f"❌ [SEND_FILE_MULTIPART_ERROR] {str(file_err)}")
                    return {"success": False, "message": f"Failed to process local file: {str(file_err)}", "data": None}
            else:
                # Use URL endpoint
                payload = {"to": normalized_to, "file_path": file_path, "wait": kwargs.get('wait_for_delivery', False)}
                response = self._make_request_with_retry("POST", f"/session/{device_id}/file", json=payload, timeout=kwargs.get('max_wait_time', 60) + 5)
            
            if response is None:
                return {"success": False, "message": "Engine no response after multiple retries (timeout/connection error)", "data": None}
                
            logger.info(f"🚀 [SEND_FILE] Status: {response.status_code}")

            if response.status_code in [200, 201, 202]:
                result_data = response.json()
                message_id = result_data.get('messageId') or f"file-{uuid.uuid4().hex[:8]}"

                if self.message_usage_service and device and not skip_credit_deduction:
                    try:
                        self.message_usage_service.deduct_credits(
                            busi_user_id=str(authenticated_user_id or device.busi_user_id),
                            message_id=message_id,
                            amount=1,  # Base64 cost
                            source="single"
                        )
                        # 🔥 LOG TO DELIVERY REPORTS (Only if not skipping)
                        self._log_message(
                            db=self.db,
                            user_id=str(authenticated_user_id or device.busi_user_id),
                            device_id=device_id,
                            to=normalized_to,
                            message=kwargs.get('caption', f"File: {os.path.basename(file_path)}"),
                            msg_type="MEDIA",
                            status="SENT"
                        )
                        self.db.commit()
                    except Exception as credit_err:
                        logger.error(f"⚠️ Credit/Report logging failed for file: {str(credit_err)}")

                return {"success": True, "message": "File sending initiated", "data": result_data}
            
            return self._handle_response_errors(response, "SEND_FILE")
        except Exception as e:
            logger.exception(f"❌ [SEND_FILE_EXCEPTION] {str(e)}")
            return {"success": False, "message": f"Service error: {str(e)}", "data": None}
    def send_file_with_caption(self, device_id: str, to: str, file_path: str, caption: str, device_name: str, skip_credit_deduction: bool = False, authenticated_user_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Send a file with a text caption"""
        logger.info(f"🚀 [SEND_FILE_CAP] To: {to}, Path: {file_path}")
        # Leverage the enhanced base64-capable send_file
        kwargs['caption'] = caption
        return self.send_file(device_id, to, file_path, device_name, skip_credit_deduction=skip_credit_deduction, authenticated_user_id=authenticated_user_id, **kwargs)

    def send_base64_file(self, device_id: str, to: str, base64_data: str, filename: Optional[str], device_name: str, skip_credit_deduction: bool = False, authenticated_user_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        normalized_to = normalize_phone(to)
        if not normalized_to:
            return {"success": False, "error": f"Invalid recipient number: {to}"}
            
        device = self._validate_device_for_api(device_id)
        
        # Clean filename
        import re
        clean_filename = filename
        if filename:
            clean_filename = re.sub(r'^[0-9a-f]{8}-[0-9a-f]{4}-.*?[0-9a-f]{12}_', '', filename)
            
        payload = {"to": normalized_to, "base64_data": base64_data, "filename": clean_filename, "caption": ""}
        response = self._make_request_with_retry("POST", f"/session/{device_id}/base64-file", json=payload, timeout=90)
        
        if response is None:
            error_msg = "Failed to send base64 file: WhatsApp Engine did not respond after retries. Check Engine status."
            logger.error(f"❌ [SEND_BASE64_FAILED] No response from engine after multiple attempts for device {device_id}")
            return {
                "success": False,
                "message": error_msg,
                "data": None
            }
        
        if response.status_code not in [200, 201, 202]:
            error_msg = f"Failed to send base64 file: HTTP {response.status_code}"
            try:
                error_detail = response.json()
                error_msg += f" - {error_detail.get('message', error_detail.get('error', 'Unknown engine error'))}"
            except:
                error_msg += f" - {response.text[:100]}"
                
            logger.error(f"❌ [SEND_BASE64_HTTP_ERROR] {error_msg}")
            return {
                "success": False,
                "message": error_msg,
                "data": None
            }

        try:
            result_data = response.json()
            message_id = result_data.get('messageId') or f"b64-{uuid.uuid4().hex[:8]}"

            # 🔥 DEDUCT CREDITS
            if self.message_usage_service and device and not skip_credit_deduction:
                try:
                    self.message_usage_service.deduct_credits(
                        busi_user_id=str(authenticated_user_id or device.busi_user_id),
                        message_id=message_id,
                        amount=1,  # Base64 cost
                        source="single"
                    )
                    # 🔥 LOG TO DELIVERY REPORTS (Only if not skipping)
                    self._log_message(
                        db=self.db,
                        user_id=str(authenticated_user_id or device.busi_user_id),
                        device_id=device_id,
                        to=normalized_to,
                        message=payload.get('caption') or f"Base64 File: {clean_filename}",
                        msg_type="MEDIA",
                        status="SENT"
                    )
                    self.db.commit()
                except Exception as credit_err:
                    logger.error(f"⚠️ Credit/Report logging failed for base64 file: {str(credit_err)}")
            
            return {
                "success": True,
                "message": "Base64 file sending initiated",
                "data": result_data
            }
        except Exception as e:
            logger.error(f"❌ [SEND_BASE64_PARSE_ERROR] {str(e)}")
            return {
                "success": False,
                "message": f"Failed to parse engine response: {str(e)}",
                "data": None
            }

    def status_check(self, device_id: str) -> Dict[str, Any]:
        device = self._validate_device_for_api(device_id)
        response = self._make_request_with_timeout("GET", f"/session/{device_id}/status", timeout=10)
        
        if response is None:
            return {"success": False, "message": "Engine unreachable (timeout/connection error)", "data": None}

        if response.status_code == 404:
            # 🔥 SYNC: Engine says session is missing, update DB
            if device:
                logger.warning(f"🔄 Syncing status for {device_id}: Engine says 404, marking as disconnected in DB")
                device.session_status = SessionStatus.disconnected
                device.last_connected_at = None
                self.db.commit()
            return {
                "success": False, 
                "message": "Device session not found in engine. Please reconnect.", 
                "status": "disconnected"
            }

        if response.status_code in [200, 201, 202]:
            return {
                "success": True,
                "message": "Status retrieved successfully",
                "data": response.json()
            }
            
        error_msg = f"Failed to check status: HTTP {response.status_code}"
        return {
            "success": False,
            "message": error_msg,
            "data": None
        }

    # -------------------------------------------------
    # MESSAGE BACKFILL / HISTORY (best-effort)
    # -------------------------------------------------
    def fetch_unread_messages(self, device_id: str, limit: int = 200) -> Dict[str, Any]:
        """
        Best-effort fetch of unread messages from engine (if engine supports it).
        Tries multiple common endpoint shapes and returns the first successful payload.

        Returns:
          - {"success": True, "data": <engine_json>, "endpoint": "<used>"}
          - {"success": False, "error": "...", "status_code": int|None}
        """
        try:
            # Don't hard-require DB presence here; only engine connectivity.
            if not self.check_engine_reachable():
                return {"success": False, "error": "WhatsApp Engine is not reachable", "status_code": None}

            # Try a few known/unofficial patterns. Engine implementations vary a lot.
            candidates = [
                (f"/session/{device_id}/unread?limit={limit}", 10),
                (f"/session/{device_id}/messages?unread=true&limit={limit}", 15),
                (f"/session/{device_id}/messages?limit={limit}", 15),  # filter unread client-side if provided
                (f"/session/{device_id}/history?unread=true&limit={limit}", 20),
                (f"/session/{device_id}/history?limit={limit}", 20),
            ]

            last_status = None
            last_err = None

            for endpoint, timeout in candidates:
                resp = self._make_request_with_timeout("GET", endpoint, timeout=timeout)
                if resp is None:
                    last_err = "no_response"
                    continue

                last_status = resp.status_code

                if resp.status_code in [200, 202]:
                    try:
                        return {"success": True, "data": resp.json(), "endpoint": endpoint}
                    except Exception as e:
                        last_err = f"invalid_json:{e}"
                        continue

                # 404 means endpoint not supported -> try next
                if resp.status_code == 404:
                    continue

                # Other client/server errors: keep trying other candidates but remember last
                try:
                    last_err = resp.json()
                except Exception:
                    last_err = resp.text[:200] if getattr(resp, "text", None) else "unknown_error"

            return {
                "success": False,
                "error": "engine_unread_endpoint_not_supported",
                "status_code": last_status,
                "details": last_err,
            }
        except Exception as e:
            logger.error(f"fetch_unread_messages error for {device_id}: {e}")
            return {"success": False, "error": str(e), "status_code": None}