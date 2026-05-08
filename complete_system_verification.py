#!/usr/bin/env python3
"""
Complete System Verification - Device Management Fix
"""
import requests
import json
import time
import uuid
from datetime import datetime

def test_system():
    print("🔍 COMPLETE SYSTEM VERIFICATION")
    print("=" * 50)
    
    # Test endpoints
    engine_health = "http://localhost:3001/health"
    backend_health = "http://localhost:8000/health"
    devices_list = "http://localhost:8000/api/devices/"
    heal_orphaned = "http://localhost:8000/api/devices/heal/orphaned"
    
    results = {}
    
    # 1. Test Engine Health
    print("\n1️⃣ Testing WhatsApp Engine...")
    try:
        response = requests.get(engine_health, timeout=5)
        if response.status_code == 200:
            data = response.json()
            results['engine'] = {
                'status': '✅ OK',
                'port': data.get('port'),
                'sessions': data.get('total_sessions', 0),
                'connected': data.get('connected', 0)
            }
            print(f"   ✅ Engine running on port {data.get('port')}")
            print(f"   📱 Sessions: {data.get('total_sessions', 0)}, Connected: {data.get('connected', 0)}")
        else:
            results['engine'] = {'status': f'❌ HTTP {response.status_code}'}
            print(f"   ❌ Engine returned HTTP {response.status_code}")
    except Exception as e:
        results['engine'] = {'status': f'❌ Error: {str(e)}'}
        print(f"   ❌ Engine connection failed: {str(e)}")
    
    # 2. Test Backend Health
    print("\n2️⃣ Testing Backend...")
    try:
        response = requests.get(backend_health, timeout=5)
        if response.status_code == 200:
            results['backend'] = {'status': '✅ OK'}
            print("   ✅ Backend running and healthy")
        else:
            results['backend'] = {'status': f'❌ HTTP {response.status_code}'}
            print(f"   ❌ Backend returned HTTP {response.status_code}")
    except Exception as e:
        results['backend'] = {'status': f'❌ Error: {str(e)}'}
        print(f"   ❌ Backend connection failed: {str(e)}")
    
    # 3. Test Device List Endpoint
    print("\n3️⃣ Testing Device List...")
    try:
        test_user_id = str(uuid.uuid4())
        response = requests.get(devices_list, params={'user_id': test_user_id}, timeout=5)
        if response.status_code == 200:
            data = response.json()
            device_count = len(data.get('devices', []))
            results['devices_list'] = {
                'status': '✅ OK',
                'count': device_count
            }
            print(f"   ✅ Device list endpoint working")
            print(f"   📊 Found {device_count} devices for test user")
        else:
            results['devices_list'] = {'status': f'❌ HTTP {response.status_code}'}
            print(f"   ❌ Device list returned HTTP {response.status_code}")
    except Exception as e:
        results['devices_list'] = {'status': f'❌ Error: {str(e)}'}
        print(f"   ❌ Device list failed: {str(e)}")
    
    # 4. Test Heal Orphaned Endpoint
    print("\n4️⃣ Testing Heal Orphaned...")
    try:
        response = requests.post(heal_orphaned, timeout=5)
        if response.status_code == 200:
            data = response.json()
            healed = data.get('message', '').split(' ')[1] if 'Healed' in data.get('message', '') else '0'
            results['heal_orphaned'] = {
                'status': '✅ OK',
                'healed': healed
            }
            print(f"   ✅ Heal orphaned endpoint working")
            print(f"   🔄 Healed {healed} orphaned devices")
        else:
            results['heal_orphaned'] = {'status': f'❌ HTTP {response.status_code}'}
            print(f"   ❌ Heal orphaned returned HTTP {response.status_code}")
    except Exception as e:
        results['heal_orphaned'] = {'status': f'❌ Error: {str(e)}'}
        print(f"   ❌ Heal orphaned failed: {str(e)}")
    
    # 5. Test Engine DELETE Session
    print("\n5️⃣ Testing Engine DELETE Session...")
    try:
        test_device_id = f"test-{uuid.uuid4().hex[:8]}"
        response = requests.delete(f"http://localhost:3001/session/{test_device_id}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            results['engine_delete'] = {
                'status': '✅ OK',
                'message': data.get('message')
            }
            print(f"   ✅ Engine DELETE endpoint working")
            print(f"   🗑️ {data.get('message')}")
        else:
            results['engine_delete'] = {'status': f'❌ HTTP {response.status_code}'}
            print(f"   ❌ Engine DELETE returned HTTP {response.status_code}")
    except Exception as e:
        results['engine_delete'] = {'status': f'❌ Error: {str(e)}'}
        print(f"   ❌ Engine DELETE failed: {str(e)}")
    
    # Final Summary
    print("\n" + "=" * 50)
    print("🎯 FINAL VERDICT")
    
    all_good = True
    for test, result in results.items():
        status = result.get('status', 'Unknown')
        if '✅' in status:
            print(f"   ✅ {test.replace('_', ' ').title()}: {status}")
        else:
            print(f"   ❌ {test.replace('_', ' ').title()}: {status}")
            all_good = False
    
    print(f"\n🚀 System Status: {'✅ ALL TESTS PASSED' if all_good else '❌ SOME TESTS FAILED'}")
    
    if all_good:
        print("\n✨ Ready for production use!")
        print("📱 Device management system is fully functional")
        print("🔄 Orphaned device healing is working")
        print("🗑️ Idempotent device deletion is working")
    else:
        print("\n⚠️ Some issues detected - please review failed tests")
    
    return all_good

if __name__ == "__main__":
    test_system()
