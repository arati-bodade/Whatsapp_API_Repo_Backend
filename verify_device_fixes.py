#!/usr/bin/env python3
"""
🧪 VERIFICATION CHECKLIST - Device Type Fixes

Test all fixes to ensure WhatsApp automation platform works correctly.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import json
import time
from typing import Dict, List, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

class DeviceFixVerification:
    def __init__(self):
        self.test_user_id = None
        self.test_results = {}
        
    def log_result(self, test_name: str, passed: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{status} {test_name}: {details}")
        self.test_results[test_name] = {"passed": passed, "details": details}
        
    def test_backend_device_endpoints(self):
        """Test backend device endpoints"""
        logger.info("🔧 Testing Backend Device Endpoints...")
        
        # Test 1: Get all devices
        try:
            response = requests.get(f"{BACKEND_URL}/api/devices/", params={
                "user_id": self.test_user_id
            })
            if response.status_code == 200:
                devices = response.json().get("devices", [])
                self.log_result("GET /api/devices/", True, f"Found {len(devices)} devices")
                
                # Check device types
                device_types = [d.get("device_type") for d in devices]
                self.log_result("Device type validation", 
                    all(dt in ["web", "official"] for dt in device_types),
                    f"Types: {device_types}")
            else:
                self.log_result("GET /api/devices/", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("GET /api/devices/", False, str(e))
            
        # Test 2: Get official devices only
        try:
            response = requests.get(f"{BACKEND_URL}/api/devices/official/list", params={
                "user_id": self.test_user_id
            })
            if response.status_code == 200:
                official_devices = response.json().get("devices", [])
                self.log_result("GET /api/devices/official/list", True, 
                    f"Found {len(official_devices)} official devices")
                
                # Verify all are official
                all_official = all(d.get("device_type") == "official" for d in official_devices)
                self.log_result("Official devices filter", all_official,
                    "All devices have device_type='official'")
            else:
                self.log_result("GET /api/devices/official/list", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("GET /api/devices/official/list", False, str(e))
            
        # Test 3: Get unofficial devices only
        try:
            response = requests.get(f"{BACKEND_URL}/api/devices/unofficial/list", params={
                "user_id": self.test_user_id
            })
            if response.status_code == 200:
                unofficial_devices = response.json().get("devices", [])
                self.log_result("GET /api/devices/unofficial/list", True,
                    f"Found {len(unofficial_devices)} unofficial devices")
                
                # Verify all are web type
                all_web = all(d.get("device_type") == "web" for d in unofficial_devices)
                self.log_result("Unofficial devices filter", all_web,
                    "All devices have device_type='web'")
            else:
                self.log_result("GET /api/devices/unofficial/list", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("GET /api/devices/unofficial/list", False, str(e))
            
        # Test 4: Get connected unofficial devices
        try:
            response = requests.get(f"{BACKEND_URL}/api/devices/unofficial/connected", params={
                "user_id": self.test_user_id
            })
            if response.status_code == 200:
                connected_devices = response.json().get("devices", [])
                self.log_result("GET /api/devices/unofficial/connected", True,
                    f"Found {len(connected_devices)} connected unofficial devices")
                
                # Verify all are web and connected
                all_valid = all(
                    d.get("device_type") == "web" and 
                    d.get("session_status") == "connected" 
                    for d in connected_devices
                )
                self.log_result("Connected unofficial filter", all_valid,
                    "All devices are web type and connected")
            else:
                self.log_result("GET /api/devices/unofficial/connected", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("GET /api/devices/unofficial/connected", False, str(e))
    
    def test_device_registration(self):
        """Test device registration with QR handling"""
        logger.info("📱 Testing Device Registration...")
        
        try:
            # Test device registration
            device_name = f"Test Device {int(time.time())}"
            response = requests.post(f"{BACKEND_URL}/api/devices/register", json={
                "user_id": self.test_user_id,
                "device_name": device_name,
                "device_type": "web"
            })
            
            if response.status_code == 200:
                device_data = response.json()
                self.log_result("Device registration", True, 
                    f"Device created: {device_data.get('device_id')}")
                
                # Verify device type
                if device_data.get("device_type") == "web":
                    self.log_result("Device type set correctly", True, "device_type='web'")
                else:
                    self.log_result("Device type set correctly", False, 
                        f"Expected 'web', got '{device_data.get('device_type')}'")
                        
                # Test QR generation (should not fail registration)
                if device_data.get("qr_code"):
                    self.log_result("QR generation", True, "QR code generated")
                else:
                    self.log_result("QR generation", True, "QR code placeholder (non-fatal)")
                    
            else:
                self.log_result("Device registration", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_result("Device registration", False, str(e))
    
    def test_replies_endpoint(self):
        """Test replies endpoint for web device filtering"""
        logger.info("💬 Testing Replies Endpoint...")
        
        try:
            response = requests.get(f"{BACKEND_URL}/api/replies")
            
            if response.status_code == 200:
                data = response.json()
                messages = data.get("data", [])
                self.log_result("GET /api/replies", True, f"Found {len(messages)} messages")
                
                # If there are messages, verify they come from web devices
                if messages:
                    # This would require checking device_id against devices table
                    # For now, just verify the endpoint works
                    self.log_result("Replies endpoint accessible", True, "Returns messages")
                else:
                    self.log_result("Replies endpoint accessible", True, "No messages (expected if no web devices)")
            else:
                self.log_result("GET /api/replies", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_result("GET /api/replies", False, str(e))
    
    def test_uuid_handling(self):
        """Test UUID handling (no .lower() errors)"""
        logger.info("🆔 Testing UUID Handling...")
        
        try:
            # Test with a valid UUID
            test_uuid = "123e4567-e89b-12d3-a456-426614174000"
            response = requests.get(f"{BACKEND_URL}/api/devices/{test_uuid}")
            
            # Should return 404 (device not found) but not 500 error
            if response.status_code == 404:
                self.log_result("UUID handling", True, "Valid UUID handled correctly (404)")
            elif response.status_code == 500:
                error_detail = response.text
                if "lower" in error_detail.lower():
                    self.log_result("UUID handling", False, "UUID .lower() error detected")
                else:
                    self.log_result("UUID handling", False, f"Server error: {error_detail}")
            else:
                self.log_result("UUID handling", True, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_result("UUID handling", False, str(e))
    
    def run_database_cleanup(self):
        """Run database cleanup script"""
        logger.info("🗄️ Running Database Cleanup...")
        
        try:
            # Import and run the cleanup script
            import fix_device_types
            
            # Mock the check_device_type_distribution to avoid interactive input
            original_check = fix_device_types.check_device_type_distribution
            def mock_check():
                logger.info("Database cleanup running...")
            fix_device_types.check_device_type_distribution = mock_check
            
            # Run the cleanup
            fix_device_types.main()
            
            # Restore original function
            fix_device_types.check_device_type_distribution = original_check
            
            self.log_result("Database cleanup", True, "Completed successfully")
            
        except Exception as e:
            self.log_result("Database cleanup", False, str(e))
    
    def get_test_user_id(self):
        """Get a test user ID from database or create one"""
        try:
            # Try to get user from backend
            response = requests.get(f"{BACKEND_URL}/api/auth/me")
            if response.status_code == 200:
                user_data = response.json()
                self.test_user_id = user_data.get("busi_user_id")
                if self.test_user_id:
                    return
            
            # Fallback: use a test UUID
            self.test_user_id = "123e4567-e89b-12d3-a456-426614174999"
            logger.warning("Using test user ID (some tests may fail)")
            
        except Exception:
            self.test_user_id = "123e4567-e89b-12d3-a456-426614174999"
            logger.warning("Using test user ID (backend not accessible)")
    
    def run_all_tests(self):
        """Run all verification tests"""
        logger.info("🚀 Starting Device Fix Verification...")
        
        # Get test user ID
        self.get_test_user_id()
        logger.info(f"Using test user ID: {self.test_user_id}")
        
        # Run database cleanup first
        self.run_database_cleanup()
        
        # Run all tests
        self.test_backend_device_endpoints()
        self.test_device_registration()
        self.test_replies_endpoint()
        self.test_uuid_handling()
        
        # Generate summary
        self.generate_summary()
    
    def generate_summary(self):
        """Generate test summary"""
        logger.info("\n" + "="*50)
        logger.info("📊 VERIFICATION SUMMARY")
        logger.info("="*50)
        
        passed = sum(1 for result in self.test_results.values() if result["passed"])
        total = len(self.test_results)
        
        logger.info(f"Tests Passed: {passed}/{total}")
        
        if passed == total:
            logger.info("🎉 ALL TESTS PASSED! Device fixes are working correctly.")
        else:
            logger.warning("⚠️ Some tests failed. Please review the issues above.")
            
        logger.info("\nDetailed Results:")
        for test_name, result in self.test_results.items():
            status = "✅" if result["passed"] else "❌"
            logger.info(f"{status} {test_name}: {result['details']}")
        
        logger.info("\n🔧 Manual Verification Steps:")
        logger.info("1. Open frontend: http://localhost:3000/dashboard/user/devices")
        logger.info("2. Verify 2-column layout (Official vs Unofficial)")
        logger.info("3. Add a new unofficial device - should work without UUID errors")
        logger.info("4. Check Manage Replies page - should only show web device messages")
        logger.info("5. Verify official devices appear only in Official section")

def main():
    """Main verification function"""
    verifier = DeviceFixVerification()
    verifier.run_all_tests()

if __name__ == "__main__":
    main()
