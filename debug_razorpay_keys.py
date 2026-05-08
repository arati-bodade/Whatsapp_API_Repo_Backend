from core.config import settings
import razorpay
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_keys():
    print("--- Razorpay Key Diagnostic ---")
    key_id = settings.RAZORPAY_KEY_ID
    key_secret = settings.RAZORPAY_KEY_SECRET
    
    print(f"Loaded Key ID: '{key_id[:8]}...' (Length: {len(key_id)})")
    print(f"Loaded Key Secret Length: {len(key_secret)}")
    
    if not key_id or not key_secret:
        print("❌ ERROR: Keys are empty! Check your .env file.")
        return

    try:
        client = razorpay.Client(auth=(key_id, key_secret))
        # Try a simple fetch to verify auth
        print("Attempting to fetch orders to verify authentication...")
        # We use a very small limit just to test auth
        client.order.all({'count': 1})
        print("✅ SUCCESS: Authentication verified with Razorpay!")
    except Exception as e:
        print(f"❌ AUTHENTICATION FAILED: {str(e)}")
        if "Authentication failed" in str(e):
            print("Tip: Your Key ID or Secret might be incorrect or for the wrong environment.")

if __name__ == "__main__":
    debug_keys()
