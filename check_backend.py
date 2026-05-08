#!/usr/bin/env python3

import requests
import sys

def check_backend():
    try:
        response = requests.get("http://localhost:3000/api/", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running and accessible!")
            return True
        else:
            print(f"❌ Backend responded with status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Backend is not running or not accessible")
        return False
    except Exception as e:
        print(f"❌ Error checking backend: {e}")
        return False

if __name__ == "__main__":
    if check_backend():
        print("🚀 Frontend should now be able to login!")
        print("Try accessing http://localhost:3000/login")
    else:
        print("🔧 Please start the backend server:")
        print("cd c:\\Users\\susha\\Desktop\\new\\whatsapp_platfrom_backent1")
        print("venv\\Scripts\\activate")
        print("python -m uvicorn main:app --reload --host 0.0.0.0 --port 3000")
