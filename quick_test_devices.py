#!/usr/bin/env python3

import requests

# Test devices API
def test_devices():
    # Login
    login_data = {"email": "amit.verma@testmail.com", "password": "Amit@12345"}
    response = requests.post("http://127.0.0.1:8000/api/busi_users/login", json=login_data)
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        return
    
    token = response.json()['access_token']
    user_id = response.json()['busi_user']['busi_user_id']
    
    # Test devices
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"http://127.0.0.1:8000/api/whatsapp/devices?user_id={user_id}", headers=headers)
    
    print(f"Devices API Status: {response.status_code}")
    if response.status_code == 200:
        devices = response.json()
        print(f"✅ Success! Found {len(devices)} devices")
        for device in devices:
            print(f"   - {device.get('device_name', 'N/A')} ({device.get('session_status', 'N/A')})")
    else:
        print(f"❌ Error: {response.text}")

if __name__ == "__main__":
    test_devices()
