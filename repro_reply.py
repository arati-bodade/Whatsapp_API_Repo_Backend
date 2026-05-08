
import requests
from db.session import get_db
from models.busi_user import BusiUser
from models.whatsapp_inbox import WhatsAppInbox
from models.device import Device
from core.security import create_access_token
from datetime import timedelta
from sqlalchemy import desc

def run_repro():
    # 1. Get DB Session
    db = next(get_db())
    
    # 2. Find a valid user with a connected device
    print("Finding valid user...")
    # Join with Device to ensure user has a device
    user = db.query(BusiUser).join(Device, Device.busi_user_id == BusiUser.busi_user_id)\
        .filter(Device.session_status == "connected")\
        .first()
        
    if not user:
        print("ERROR: No user found with connected device.")
        return

    print(f"User Found: {user.username} ({user.busi_user_id})")

    # 3. Find a valid message for this user's device
    print("Finding valid message...")
    # Get user's device IDs
    devices = db.query(Device).filter(
        Device.busi_user_id == user.busi_user_id,
        Device.session_status == "connected"
    ).all()
    device_ids = [d.device_id for d in devices]
    
    message = db.query(WhatsAppInbox).filter(
        WhatsAppInbox.device_id.in_(device_ids),
        WhatsAppInbox.chat_type == "individual"
    ).order_by(desc(WhatsAppInbox.incoming_time)).first()

    if not message:
        print("ERROR: No inbox message found for this user's devices.")
        return

    print(f"Message Found: ID={message.id}, Phone={message.phone_number}, Device={message.device_id}")

    # 4. Generate Token
    print("Generating Token...")
    access_token = create_access_token(
        data={"sub": str(user.busi_user_id)},
        expires_delta=timedelta(minutes=30)
    )
    
    # 5. Send Request
    url = "http://127.0.0.1:8000/api/replies/send"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "message_id": str(message.id),
        "reply_text": "Test reply from repro script."
    }

    print(f"Sending POST to {url}...")
    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    run_repro()
