import httpx
import logging
from core.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.service_id = settings.EMAILJS_SERVICE_ID
        self.template_id = settings.EMAILJS_TEMPLATE_ID
        self.public_key = settings.EMAILJS_PUBLIC_KEY
        self.private_key = settings.EMAILJS_PRIVATE_KEY
        self.api_url = "https://api.emailjs.com/api/v1.0/email/send"

    async def send_password_reset_email(self, email: str, reset_link: str):
        """
        Send password reset email via EmailJS REST API
        """
        if not all([self.service_id, self.template_id, self.public_key]):
            logger.error("EmailJS credentials not fully configured. Cannot send email.")
            return False

        try:
            # Prepare EmailJS payload
            payload = {
                "service_id": self.service_id,
                "template_id": self.template_id,
                "user_id": self.public_key,
                "accessToken": self.private_key,
                "template_params": {
                    "to_email": email,
                    "reset_link": reset_link,
                    "to_name": email.split('@')[0],
                    "subject": "Password Reset Request - WhatsApp Platform"
                }
            }

            logger.info(f"Sending EmailJS request for {email}...")
            
            # Use HTTP/1.1 specifically to avoid potential H2 hangs
            async with httpx.AsyncClient(http2=False, timeout=20.0) as client:
                response = await client.post(self.api_url, json=payload)
                
                if response.status_code == 200:
                    logger.info(f"✅ Password reset email sent successfully via EmailJS to {email}")
                    return True
                else:
                    logger.error(f"❌ EmailJS API error: {response.status_code} - {response.text}")
                    return False

        except Exception as e:
            logger.error(f"❌ Failed to send email via EmailJS to {email}: {str(e)}")
            return False

    async def send_credit_shortage_alert(self, reseller_email: str, sub_user_name: str, plan_name: str, shortage: float):
        """
        Send credit shortage alert to reseller
        """
        template_id = settings.EMAILJS_ALERT_TEMPLATE_ID or self.template_id
        if not all([self.service_id, template_id, self.public_key]):
            logger.error("EmailJS credentials not fully configured for alerts.")
            return False

        try:
            payload = {
                "service_id": self.service_id,
                "template_id": template_id,
                "user_id": self.public_key,
                "accessToken": self.private_key,
                "template_params": {
                    "to_email": reseller_email,
                    "to_name": reseller_email.split('@')[0],
                    "sub_user_name": sub_user_name,
                    "plan_name": plan_name,
                    "shortage": str(shortage),
                    "dashboard_url": f"{settings.FRONTEND_URL}/dashboard/reseller/alerts",
                    "subject": "CRITICAL: Insufficient Credits for Sub-user Purchase"
                }
            }
            
            async with httpx.AsyncClient(http2=False, timeout=20.0) as client:
                response = await client.post(self.api_url, json=payload)
                return response.status_code == 200
        except Exception as e:
            logger.error(f"❌ Failed to send alert email: {str(e)}")
            return False

email_service = EmailService()
