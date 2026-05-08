import requests
import json

BASE_URL = "http://localhost:8000"

def test_failing_endpoints():
    print("--- API ERROR DIAGNOSTIC ---")
    
    # 1. Login to get token
    login_url = f"{BASE_URL}/api/busi_users/login"
    login_data = {
        "email": "lungeom39@gmail.com",
        "password": "user123"
    }
    
    print(f"Logging in as {login_data['email']}...")
    try:
        response = requests.post(login_url, json=login_data)
        if response.status_code != 200:
            print(f"ERROR: Login Failed: {response.status_code} - {response.text}")
            return
        
        token = response.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        print("SUCCESS: Login Successful.")
        
        # 2. Test /api/busi_users/me
        print("\nTesting GET /api/busi_users/me ...")
        res = requests.get(f"{BASE_URL}/api/busi_users/me", headers=headers)
        print(f"Status: {res.status_code}")
        if res.status_code == 500:
            print(f"FAIL: {res.text}")
        else:
            print(f"SUCCESS: {res.status_code}")
            
        # 3. Test /api/devices/unofficial/list
        print("\nTesting GET /api/devices/unofficial/list ...")
        res = requests.get(f"{BASE_URL}/api/devices/unofficial/list", headers=headers)
        print(f"Status: {res.status_code}")
        if res.status_code == 500:
            print(f"FAIL: {res.text}")
        else:
            print(f"SUCCESS: {res.status_code}")
            
        # 4. Test google-sheets/triggers/all
        print("\nTesting GET /api/google-sheets/triggers/all ...")
        res = requests.get(f"{BASE_URL}/api/google-sheets/triggers/all", headers=headers)
        print(f"Status: {res.status_code}")
        if res.status_code == 500:
            print(f"FAIL: {res.text}")
        else:
            print(f"SUCCESS: {res.status_code}")

    except Exception as e:
        print(f"CRITICAL: Diagnostic script error: {e}")

if __name__ == "__main__":
    test_failing_endpoints()
