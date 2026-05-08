import requests
import json
import uuid

USER_ID = "d1bc821d-9297-486c-9484-6ec4dd05cb54"
BASE_URL = "http://127.0.0.1:8000/api/whatsapp"

def verify_full_flow():
    unique = uuid.uuid4().hex[:6]
    payload = {
        "device_name": f"TestDevice_{unique}",
        "device_type": "web",
        "user_id": USER_ID,
        "phone_number": "1234567890"
    }
    
    try:
        resp = requests.post(f"{BASE_URL}/add-device", json=payload)
        if resp.status_code != 200:
            with open("last_error.txt", "w") as f:
                f.write(resp.text)
            print("Wrote error to last_error.txt")
        else:
            print("Success")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify_full_flow()
