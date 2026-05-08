
import requests
from db.session import get_db
from models.busi_user import BusiUser
from models.device import Device
from core.security import create_access_token
from datetime import timedelta

def run_repro():
    # 1. Get DB Session
    db = next(get_db())
    
    # 2. Find a valid user (any active user)
    print("Finding valid user...")
    user = db.query(BusiUser).first()
        
    if not user:
        print("ERROR: No user found.")
        return

    print(f"User Found: {user.username} ({user.busi_user_id})")

    # 3. Generate Token
    print("Generating Token...")
    access_token = create_access_token(
        data={"sub": str(user.busi_user_id)},
        expires_delta=timedelta(minutes=30)
    )
    
    # 4. Send Request
    url = "http://127.0.0.1:8000/api/replies/mark-read"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "phone_number": "911234567890" # Dummy phone number
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
