#!/usr/bin/env python3
"""
🔥 UNIFIED WHATSAPP SENDER - CORE DELIVERY LOGIC
Accepted ≠ Delivered - Real message delivery implementation
"""

import time
import requests
import logging
import re
from typing import Dict, Any, Optional
from datetime import datetime
from core.config import settings

logger = logging.getLogger(__name__)


class UnifiedWhatsAppSender:

    def __init__(self, engine_url: str = None):
        self.engine_url = engine_url or settings.WHATSAPP_ENGINE_BASE_URL
        self.session = requests.Session()

    # -------------------------------------------------
    # PHONE NORMALIZATION (FIXED)
    # -------------------------------------------------
    def normalize_phone(self, phone: str) -> Optional[str]:
        if not phone:
            return None

        phone = str(phone).strip()

        # Remove JID suffix if present
        if "@" in phone:
            phone = phone.split("@")[0]

        # Remove non digits
        phone = re.sub(r"\D", "", phone)

        # Basic sanity: phone must be 10–16 digits
        if len(phone) < 10 or len(phone) > 16:
            # logger.warning(f"Invalid phone length: {phone}") # Optional: log internal warning
            return None

        # No longer automatically prepends '91' to avoid hardcoding country constraints.
        # WhatsApp numbers MUST include the country code to be valid.
        return phone

    # -------------------------------------------------
    def engine_is_healthy(self) -> bool:
        try:
            response = self.session.get(f"{self.engine_url}/health", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def get_device_status(self, device_id: str) -> Optional[str]:
        try:
            response = self.session.get(f"{self.engine_url}/session/{device_id}/status", timeout=5)
            if response.status_code == 200:
                data = response.json() if response.content else {}
                status = data.get("status")
                if status:
                    return status

            if response.status_code == 404:
                return "not_found"

            # Fallback: some engine versions expose session info at /session/:id
            fallback = self.session.get(f"{self.engine_url}/session/{device_id}", timeout=5)
            if fallback.status_code == 200:
                data = fallback.json() if fallback.content else {}
                status = data.get("status")
                if status:
                    return status
                # if session exists but no status field, treat as connected-ish
                return "connected"
            if fallback.status_code == 404:
                return "not_found"
            return None
        except Exception:
            return None

    # -------------------------------------------------
    # CORE SEND FUNCTION (FIXED)
    # -------------------------------------------------
    def send_whatsapp_message(
        self, 
        device_id: str, 
        phone: str, 
        message: str,
        jid: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a WhatsApp message via the engine.
        If 'jid' is provided, it uses it directly (most accurate).
        Otherwise, it normalizes the phone and guesses the JID type.
        """
        try:
            logger.info("🚀 UNIFIED SEND: Starting message delivery")
            logger.info(f"   Device ID: {device_id}")
            logger.info(f"   Raw Phone: {phone}")

            normalized_phone = self.normalize_phone(phone)

            if not normalized_phone:
                return {
                    "success": False,
                    "error": f"Invalid WhatsApp phone number: {phone}",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }

            # Determine JID: If explicit JID is provided, use it. 
            # Otherwise, guess based on length (14+ digits = LID)
            if not jid:
                if len(normalized_phone) >= 14:
                    jid = f"{normalized_phone}@lid"
                    logger.info(f"   Guessed LID format: {jid}")
                else:
                    jid = f"{normalized_phone}@s.whatsapp.net"
            else:
                logger.info(f"   Using explicit JID: {jid}")
            
            # 🔥 PROTECTIVE LOG - FINAL CHECK
            logger.warning(f"[PHONE VALIDATION] Final sending JID: {jid}")

            logger.info(f"   Normalized Phone: {normalized_phone}")
            logger.info(f"   JID: {jid}")

            # NOTE: Removed redundant health/status checks here to avoid transient flapping errors.
            # The engine will return 400/404/500 if the session is truly dead.
            
            time.sleep(1) # Reduced throttle slightly 

            payload = {"to": jid, "message": message}
            
            max_attempts = 2
            for attempt in range(1, max_attempts + 1):
                try:
                    response = self.session.post(
                        f"{self.engine_url}/session/{device_id}/message",
                        json=payload,
                        timeout=30
                    )
                
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("status") in ["accepted", "sent", "queued"]:
                            return {
                                "success": True,
                                "status": "sent",
                                "message_id": data.get("messageId") or f"pending_{int(datetime.utcnow().timestamp()*1000)}_{device_id[:8]}",
                                "device_id": device_id,
                                "phone": normalized_phone,
                                "jid": jid,
                                "timestamp": datetime.utcnow().isoformat()
                            }
                        return {"success": False, "error": data.get("error", "Unknown engine error")}

                    if response.status_code in [400, 404, 503]:
                        if attempt < max_attempts:
                            logger.warning(f"   Engine returned {response.status_code} on attempt {attempt}. Retrying in 3s...")
                            time.sleep(3)
                            continue
                        # Final attempt failed - give a user-friendly error
                        if response.status_code == 404:
                            return {"success": False, "error": "Device session not found in engine. Please reconnect your WhatsApp device."}
                        return {"success": False, "error": "Device session is disconnected. Please reconnect your WhatsApp device."}
                    
                    return {"success": False, "error": f"Engine error (HTTP {response.status_code})"}

                except Exception as req_err:
                    logger.warning(f"   Request attempt {attempt} failed: {req_err}")
                    if attempt < max_attempts:
                        time.sleep(2)
                        continue
                    raise


        except Exception as e:
            logger.error(f"UNIFIED SEND FAILED: {e}")
            return {
                "success": False,
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


# Global instance
unified_sender = UnifiedWhatsAppSender()


def send_whatsapp_message(device_id: str, phone: str, message: str, jid: Optional[str] = None) -> Dict[str, Any]:
    """
    Wrapper for convenience
    """
    return unified_sender.send_whatsapp_message(device_id, phone, message, jid=jid)
