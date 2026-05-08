import requests
import json

BASE_URL = "http://localhost:8000/api"

def run_check():
    print("Checking login...")
    try:
        resp = requests.post(f"{BASE_URL}/resellers/login", json={
            "email": "test_verification@example.com",
            "password": "new_password" 
        }, timeout=5)
        
        if resp.status_code == 401:
             resp = requests.post(f"{BASE_URL}/resellers/login", json={
                "email": "test_verification@example.com",
                "password": "old_password"
            }, timeout=5)
            
        if resp.status_code != 200:
            print(f"Login failed: {resp.status_code} {resp.text}")
            return

        token = resp.json()["access_token"]
        print("Login OK. Checking /me...")
        
        resp = requests.get(f"{BASE_URL}/resellers/me", headers={
            "Authorization": f"Bearer {token}"
        }, timeout=5)
        
        print(f"Me Status: {resp.status_code}")
        print(f"Me Body: {resp.text}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_check()
