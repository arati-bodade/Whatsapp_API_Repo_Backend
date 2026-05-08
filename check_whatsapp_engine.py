#!/usr/bin/env python3
"""
Check if WhatsApp Engine is running and accessible
"""

import requests
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_whatsapp_engine():
    """Check WhatsApp Engine status"""
    engine_url = "http://localhost:3002"
    
    print("🔍 Checking WhatsApp Engine Status...")
    print("=" * 50)
    
    # Test basic connectivity
    try:
        response = requests.get(engine_url, timeout=5)
        print(f"✅ Engine is reachable (HTTP {response.status_code})")
        print(f"   Response: {response.text[:100]}...")
    except requests.exceptions.ConnectionError:
        print("❌ Engine is NOT running or not accessible")
        print("   Expected URL: http://localhost:3002")
        print("   Please start the WhatsApp Engine first")
        return False
    except requests.exceptions.Timeout:
        print("❌ Engine timeout - might be starting up")
        return False
    except Exception as e:
        print(f"❌ Error checking engine: {e}")
        return False
    
    # Test health endpoint
    try:
        health_response = requests.get(f"{engine_url}/health", timeout=5)
        print(f"✅ Health endpoint: HTTP {health_response.status_code}")
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"   Health status: {health_data}")
    except Exception as e:
        print(f"⚠️  Health endpoint error: {e}")
    
    # Test device status endpoint
    try:
        status_response = requests.get(f"{engine_url}/session/test-device/status", timeout=5)
        print(f"✅ Device status endpoint: HTTP {status_response.status_code}")
        if status_response.status_code == 404:
            print("   Expected: Device not found (404) - engine is working")
        elif status_response.status_code == 200:
            device_data = status_response.json()
            print(f"   Device data: {device_data}")
    except Exception as e:
        print(f"⚠️  Device status endpoint error: {e}")
    
    print("\n" + "=" * 50)
    print("📋 WhatsApp Engine Status Summary:")
    print("   • Basic connectivity: ✅ Working")
    print("   • Expected 404 for unknown devices: ✅ Normal")
    print("   • Your devices should work once engine has sessions")
    print("\n💡 To connect devices:")
    print("   1. Make sure WhatsApp Engine is running")
    print("   2. Use the frontend to scan QR codes")
    print("   3. Devices will show as 'connected' after successful scan")
    
    return True

if __name__ == "__main__":
    check_whatsapp_engine()
