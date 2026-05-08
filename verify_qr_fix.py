import requests
import uuid
import time

BASE_URL = "http://localhost:8000/api"
USER_ID = "550e8400-e29b-41d4-a716-446655440000"

def test_qr_flow():
    print("🚀 Starting QR Flow Verification...")
    
    # 1. Register Device
    device_name = f"Test Device {uuid.uuid4().hex[:6]}"
    print(f"1️⃣ Registering device '{device_name}'...")
    
    try:
        res = requests.post(f"{BASE_URL}/devices/register", json={"user_id": USER_ID, "device_name": device_name})
        if res.status_code != 200:
            print(f"❌ Registration Failed: {res.status_code} - {res.text}")
            return
        
        data = res.json()
        device_id = data["device_id"]
        qr_code = data.get("qr_code")
        
        print(f"✅ Device Registered: {device_id}")
        
        if qr_code and "base64" in qr_code or "mock" in qr_code or "data:image" in qr_code:
            print(f"✅ SUCCESS: QR Code received during registration!")
            print(f"   QR Preview: {qr_code[:50]}...")
            return
        else:
            print(f"⚠️  No QR in registration response. Trying explicit fetch...")

    except Exception as e:
        print(f"❌ Registration Error: {e}")
        return

    # 2. Fetch QR Code (Waiting for cooldown)
    print("⏳ Waiting 20s for cooldown...")
    time.sleep(20)
    
    print(f"2️⃣ Fetching QR Code for {device_id}...")
    try:
        res = requests.get(f"{BASE_URL}/devices/{device_id}/qr")
        
        if res.status_code == 200:
            qr_data = res.json()
            print(f"✅ SUCCESS! QR Code Retrieved.")
            print(f"   Status: {qr_data.get('status')}")
        else:
            print(f"❌ QR Fetch Failed: {res.status_code}")
            print(f"   Response: {res.text}")
            
    except Exception as e:
        print(f"❌ QR Fetch Error: {e}")

if __name__ == "__main__":
    test_qr_flow()
