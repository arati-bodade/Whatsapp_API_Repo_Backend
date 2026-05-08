import logging
import razorpay
from typing import Dict, Any, Optional
from core.config import settings

logger = logging.getLogger(__name__)

class PaymentService:
    def __init__(self):
        self.key_id = settings.RAZORPAY_KEY_ID or ""
        self.key_secret = settings.RAZORPAY_KEY_SECRET or ""
        
        if not self.key_id or not self.key_secret:
             logger.error(f"⚠️ Razorpay Keys are MISSING from Settings! ID: {len(self.key_id)} chars, Secret: {len(self.key_secret)} chars")
        else:
             logger.info(f"✅ Razorpay Payment Service initialized with Key ID: {self.key_id[:8]}... (Total: {len(self.key_id)} chars)")
             
        self.client = razorpay.Client(
            auth=(self.key_id, self.key_secret)
        )

    def create_order(self, amount: float, currency: str = "INR", notes: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a Razorpay order.
        Amount should be in the smallest currency unit (e.g., paise for INR).
        """
        try:
            # Razorpay expects amount in paise
            amount_in_paise = int(float(amount) * 100)
            
            data = {
                "amount": amount_in_paise,
                "currency": currency,
                "notes": notes or {}
            }
            
            order = self.client.order.create(data=data)
            logger.info(f"Razorpay Order Created: {order['id']}")
            return {"success": True, "order": order}
        except Exception as e:
            logger.error(f"Razorpay order creation failed: {str(e)}")
            return {"success": False, "error": str(e)}

    def verify_signature(self, razorpay_order_id: str, razorpay_payment_id: str, razorpay_signature: str) -> bool:
        """
        Verify the Razorpay payment signature.
        """
        try:
            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            }
            self.client.utility.verify_payment_signature(params_dict)
            logger.info(f"Razorpay signature verified for order {razorpay_order_id}")
            return True
        except Exception as e:
            logger.error(f"Razorpay signature verification failed: {str(e)}")
            return False

    def get_payment_details(self, payment_id: str) -> Dict[str, Any]:
        """
        Fetch details of a specific payment.
        """
        try:
            payment = self.client.payment.fetch(payment_id)
            return payment
        except Exception as e:
            logger.error(f"Failed to fetch Razorpay payment {payment_id}: {str(e)}")
            return {}
