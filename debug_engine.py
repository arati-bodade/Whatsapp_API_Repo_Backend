
import requests

ENGINE_URL = "http://localhost:3002"
DEVICE_ID = "6f73e184-0e78-42a4-a325-56d4eac74856"

def check_engine():
    print(f"Checking Engine at {ENGINE_URL}...")
    
    # 1. Health
    try:
        resp = requests.get(f"{ENGINE_URL}/health", timeout=5)
        print(f"Health: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"Health Check Failed: {e}")

    # 2. Device Status
    print(f"Checking Session Status for {DEVICE_ID}...")
    try:
        resp = requests.get(f"{ENGINE_URL}/session/{DEVICE_ID}/status", timeout=5)
        print(f"Status Code: {resp.status_code}")
        print(f"Response: {resp.text}")
    except Exception as e:
        print(f"Session Status Check Failed: {e}")

if __name__ == "__main__":
    check_engine()
