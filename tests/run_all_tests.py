#!/usr/bin/env python3

"""
Run all tests
"""

import sys
import os
import importlib.util

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_test_file(test_file):
    """Run a single test file."""
    try:
        # Import the test module
        spec = importlib.util.spec_from_file_location("test_module", test_file)
        test_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(test_module)
        
        # Run the main function if it exists
        if hasattr(test_module, '__main__') or hasattr(test_module, 'main'):
            if hasattr(test_module, 'main'):
                test_module.main()
            else:
                # Run all test functions
                for attr_name in dir(test_module):
                    if attr_name.startswith('test_') and callable(getattr(test_module, attr_name)):
                        getattr(test_module, attr_name)()
        
        return True, None
    except Exception as e:
        return False, str(e)

def main():
    """Run all test files."""
    print("🧪 Running All Tests")
    print("=" * 50)
    
    test_files = [
        "test_main.py",
        "test_database.py", 
        "test_services.py",
        "test_logout_apis.py",
        "test_db_connection.py"
    ]
    
    tests_dir = os.path.dirname(os.path.abspath(__file__))
    passed = 0
    failed = 0
    
    for test_file in test_files:
        test_path = os.path.join(tests_dir, test_file)
        
        if os.path.exists(test_path):
            print(f"\n📋 Running {test_file}...")
            success, error = run_test_file(test_path)
            
            if success:
                print(f"✅ {test_file} PASSED")
                passed += 1
            else:
                print(f"❌ {test_file} FAILED: {error}")
                failed += 1
        else:
            print(f"⚠️  {test_file} not found")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Total: {passed + failed}")
    
    if failed == 0:
        print("🎉 All tests passed!")
        return True
    else:
        print("💥 Some tests failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
