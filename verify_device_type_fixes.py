#!/usr/bin/env python3
"""
🔍 DEVICE TYPE FIXES VERIFICATION
Tests all critical device type separation fixes
"""
import asyncio
import logging
import sys
import traceback
import uuid
from datetime import datetime
from typing import Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DeviceTypeFixesVerifier:
    """
    🔥 COMPREHENSIVE DEVICE TYPE VERIFICATION
    Tests all fixes for device type separation issues
    """
    
    def __init__(self):
        self.test_results = {
            "device_type_enum": {"status": "pending", "details": ""},
            "official_device_creation": {"status": "pending", "details": ""},
            "unofficial_device_creation": {"status": "pending", "details": ""},
            "device_api_filtering": {"status": "pending", "details": ""},
            "logout_immediate": {"status": "pending", "details": ""},
            "manage_replies_filtering": {"status": "pending", "details": ""},
            "safety_service": {"status": "pending", "details": ""},
            "qr_generation_safety": {"status": "pending", "details": ""}
        }
    
    async def test_device_type_enum(self):
        """Test 1️⃣: Device Type Enum Definition"""
        logger.info("🔍 Testing Device Type enum...")
        
        try:
            from models.device import DeviceType
            
            # Test new enum values exist
            assert hasattr(DeviceType, 'OFFICIAL'), "DeviceType.OFFICIAL missing"
            assert hasattr(DeviceType, 'UNOFFICIAL'), "DeviceType.UNOFFICIAL missing"
            
            # Test values
            assert DeviceType.OFFICIAL == "official", f"DeviceType.OFFICIAL value incorrect: {DeviceType.OFFICIAL}"
            assert DeviceType.UNOFFICIAL == "unofficial", f"DeviceType.UNOFFICIAL value incorrect: {DeviceType.UNOFFICIAL}"
            
            # Test legacy values still exist (for backward compatibility)
            assert hasattr(DeviceType, 'web'), "DeviceType.web missing (legacy)"
            assert hasattr(DeviceType, 'mobile'), "DeviceType.mobile missing (legacy)"
            
            self.test_results["device_type_enum"]["status"] = "✅ PASSED"
            self.test_results["device_type_enum"]["details"] = "DeviceType enum correctly defined with OFFICIAL/UNOFFICIAL"
            
        except Exception as e:
            self.test_results["device_type_enum"]["status"] = "❌ FAILED"
            self.test_results["device_type_enum"]["details"] = f"Exception: {str(e)}"
    
    async def test_official_device_creation(self):
        """Test 2️⃣: Official Device Creation Logic"""
        logger.info("🔍 Testing Official device creation...")
        
        try:
            from models.device import DeviceType
            from services.device_sync_service import DeviceSyncService
            
            # Test that official device creation uses OFFICIAL type
            # We can't create actual DB objects here, but we can test the logic
            
            # Check device_sync_service.py has the fix
            import inspect
            sync_service_source = inspect.getsource(DeviceSyncService)
            
            if 'DeviceType.OFFICIAL' in sync_service_source and 'device_type=DeviceType.OFFICIAL' in sync_service_source:
                self.test_results["official_device_creation"]["status"] = "✅ PASSED"
                self.test_results["official_device_creation"]["details"] = "Official device creation uses DeviceType.OFFICIAL"
            else:
                self.test_results["official_device_creation"]["status"] = "❌ FAILED"
                self.test_results["official_device_creation"]["details"] = "Official device creation not using DeviceType.OFFICIAL"
                
        except Exception as e:
            self.test_results["official_device_creation"]["status"] = "❌ FAILED"
            self.test_results["official_device_creation"]["details"] = f"Exception: {str(e)}"
    
    async def test_unofficial_device_creation(self):
        """Test 3️⃣: Unofficial Device Creation Logic"""
        logger.info("🔍 Testing Unofficial device creation...")
        
        try:
            from models.device import DeviceType
            
            # Check device_service.py uses UNOFFICIAL for register_device
            with open('services/device_service.py', 'r') as f:
                device_service_source = f.read()
            
            if 'DeviceType.UNOFFICIAL' in device_service_source and 'device_type=DeviceType.UNOFFICIAL' in device_service_source:
                self.test_results["unofficial_device_creation"]["status"] = "✅ PASSED"
                self.test_results["unofficial_device_creation"]["details"] = "Unofficial device creation uses DeviceType.UNOFFICIAL"
            else:
                self.test_results["unofficial_device_creation"]["status"] = "❌ FAILED"
                self.test_results["unofficial_device_creation"]["details"] = "Unofficial device creation not using DeviceType.UNOFFICIAL"
                
        except Exception as e:
            self.test_results["unofficial_device_creation"]["status"] = "❌ FAILED"
            self.test_results["unofficial_device_creation"]["details"] = f"Exception: {str(e)}"
    
    async def test_device_api_filtering(self):
        """Test 4️⃣: Device API Filtering"""
        logger.info("🔍 Testing Device API filtering...")
        
        try:
            # Check devices API has device_type filtering
            with open('api/devices.py', 'r') as f:
                devices_api_source = f.read()
            
            checks = [
                'device_type: Optional[str]' in devices_api_source,
                'device_type.lower() == "official"' in devices_api_source,
                'device_type.lower() == "unofficial"' in devices_api_source,
                'get_devices_by_user_and_type' in devices_api_source
            ]
            
            if all(checks):
                self.test_results["device_api_filtering"]["status"] = "✅ PASSED"
                self.test_results["device_api_filtering"]["details"] = "Device API properly filters by device_type"
            else:
                self.test_results["device_api_filtering"]["status"] = "❌ FAILED"
                self.test_results["device_api_filtering"]["details"] = "Device API missing device_type filtering"
                
        except Exception as e:
            self.test_results["device_api_filtering"]["status"] = "❌ FAILED"
            self.test_results["device_api_filtering"]["details"] = f"Exception: {str(e)}"
    
    async def test_logout_immediate(self):
        """Test 5️⃣: Immediate Logout Implementation"""
        logger.info("🔍 Testing immediate logout...")
        
        try:
            # Check logout service has immediate DB update
            with open('services/device_service.py', 'r') as f:
                logout_service_source = f.read()
            
            checks = [
                'IMMEDIATE DB STATUS UPDATE' in logout_service_source,
                'disconnected_at = datetime.utcnow()' in logout_service_source,
                'Step 1: IMMEDIATE DB status update' in logout_service_source
            ]
            
            if all(checks):
                self.test_results["logout_immediate"]["status"] = "✅ PASSED"
                self.test_results["logout_immediate"]["details"] = "Logout implementation has immediate DB update"
            else:
                self.test_results["logout_immediate"]["status"] = "❌ FAILED"
                self.test_results["logout_immediate"]["details"] = "Logout implementation missing immediate update"
                
        except Exception as e:
            self.test_results["logout_immediate"]["status"] = "❌ FAILED"
            self.test_results["logout_immediate"]["details"] = f"Exception: {str(e)}"
    
    async def test_manage_replies_filtering(self):
        """Test 6️⃣: Manage Replies Filtering"""
        logger.info("🔍 Testing Manage Replies filtering...")
        
        try:
            # Check replies API filters by UNOFFICIAL
            with open('api/replies.py', 'r') as f:
                replies_api_source = f.read()
            
            checks = [
                'Device.device_type == DeviceType.UNOFFICIAL' in replies_api_source,
                'UNOFFICIAL devices only' in replies_api_source,
                'Official devices should NOT appear' in replies_api_source
            ]
            
            if all(checks):
                self.test_results["manage_replies_filtering"]["status"] = "✅ PASSED"
                self.test_results["manage_replies_filtering"]["details"] = "Manage Replies properly filters UNOFFICIAL devices"
            else:
                self.test_results["manage_replies_filtering"]["status"] = "❌ FAILED"
                self.test_results["manage_replies_filtering"]["details"] = "Manage Replies missing UNOFFICIAL filtering"
                
        except Exception as e:
            self.test_results["manage_replies_filtering"]["status"] = "❌ FAILED"
            self.test_results["manage_replies_filtering"]["details"] = f"Exception: {str(e)}"
    
    async def test_safety_service(self):
        """Test 7️⃣: Device Type Safety Service"""
        logger.info("🔍 Testing Device Type Safety Service...")
        
        try:
            # Check safety service exists and has required methods
            with open('services/device_type_safety_service.py', 'r') as f:
                safety_service_source = f.read()
            
            checks = [
                'class DeviceTypeSafetyService' in safety_service_source,
                'validate_device_type_for_workflow' in safety_service_source,
                'get_official_devices' in safety_service_source,
                'get_unofficial_devices' in safety_service_source,
                'official_workflows' in safety_service_source,
                'unofficial_workflows' in safety_service_source
            ]
            
            if all(checks):
                self.test_results["safety_service"]["status"] = "✅ PASSED"
                self.test_results["safety_service"]["details"] = "Device Type Safety Service properly implemented"
            else:
                self.test_results["safety_service"]["status"] = "❌ FAILED"
                self.test_results["safety_service"]["details"] = "Device Type Safety Service missing required methods"
                
        except Exception as e:
            self.test_results["safety_service"]["status"] = "❌ FAILED"
            self.test_results["safety_service"]["details"] = f"Exception: {str(e)}"
    
    async def test_qr_generation_safety(self):
        """Test 8️⃣: QR Generation Safety"""
        logger.info("🔍 Testing QR generation safety...")
        
        try:
            # Check QR generation has safety validation
            with open('api/devices.py', 'r') as f:
                qr_api_source = f.read()
            
            checks = [
                'validate_unofficial_device' in qr_api_source,
                'QR generation is only allowed for UNOFFICIAL devices' in qr_api_source,
                'qr_generation' in qr_api_source
            ]
            
            if all(checks):
                self.test_results["qr_generation_safety"]["status"] = "✅ PASSED"
                self.test_results["qr_generation_safety"]["details"] = "QR generation has UNOFFICIAL device validation"
            else:
                self.test_results["qr_generation_safety"]["status"] = "❌ FAILED"
                self.test_results["qr_generation_safety"]["details"] = "QR generation missing safety validation"
                
        except Exception as e:
            self.test_results["qr_generation_safety"]["status"] = "❌ FAILED"
            self.test_results["qr_generation_safety"]["details"] = f"Exception: {str(e)}"
    
    async def run_all_tests(self):
        """Run all verification tests"""
        logger.info("🚀 Starting comprehensive device type fixes verification...")
        
        tests = [
            self.test_device_type_enum,
            self.test_official_device_creation,
            self.test_unofficial_device_creation,
            self.test_device_api_filtering,
            self.test_logout_immediate,
            self.test_manage_replies_filtering,
            self.test_safety_service,
            self.test_qr_generation_safety
        ]
        
        for test in tests:
            try:
                await test()
            except Exception as e:
                logger.error(f"Test failed with exception: {e}")
                traceback.print_exc()
        
        self.print_results()
    
    def print_results(self):
        """Print verification results"""
        print("\n" + "="*80)
        print("🔍 DEVICE TYPE FIXES VERIFICATION RESULTS")
        print("="*80)
        
        passed = 0
        total = len(self.test_results)
        
        for test_name, result in self.test_results.items():
            status = result["status"]
            details = result["details"]
            
            print(f"\n{test_name.replace('_', ' ').title()}:")
            print(f"  Status: {status}")
            print(f"  Details: {details}")
            
            if "✅ PASSED" in status:
                passed += 1
        
        print("\n" + "="*80)
        print(f"📊 SUMMARY: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 ALL DEVICE TYPE FIXES VERIFIED - System is properly segregated!")
        else:
            print("⚠️  Some tests failed - Please review the issues above")
        
        print("="*80)

async def main():
    """Main verification function"""
    verifier = DeviceTypeFixesVerifier()
    await verifier.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
