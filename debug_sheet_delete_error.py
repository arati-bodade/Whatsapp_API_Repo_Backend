#!/usr/bin/env python3

"""
Debug script for Google Sheet delete errors
Run this to test the delete endpoint and see detailed error information
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from main import app
import uuid
import json

# Create test client
client = TestClient(app)

def debug_delete_sheet():
    """Debug the delete sheet endpoint with detailed error reporting"""
    
    print("🔍 Debugging Google Sheet Delete Endpoint")
    print("=" * 50)
    
    # Test 1: Check if endpoint exists
    print("\n1. Testing endpoint existence:")
    
    # Try to access the endpoint options
    try:
        response = client.options("/api/google-sheets/test-sheet-id")
        print(f"   OPTIONS Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ DELETE endpoint exists")
        else:
            print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 2: Test with invalid ID
    print("\n2. Testing with invalid sheet ID:")
    
    try:
        response = client.delete("/api/google-sheets/invalid-id")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        
        if response.status_code == 401:
            print("   ✅ Authentication required (expected)")
        elif response.status_code == 500:
            print("   ❌ Server error - this might be the issue")
            print("   Check backend logs for detailed error")
        elif response.status_code == 404:
            print("   ✅ Not found error (expected for invalid ID)")
            
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 3: Test with valid UUID format
    print("\n3. Testing with valid UUID format:")
    
    test_uuid = str(uuid.uuid4())
    try:
        response = client.delete(f"/api/google-sheets/{test_uuid}")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        
        if response.status_code == 401:
            print("   ✅ Authentication required (expected)")
        elif response.status_code == 500:
            print("   ❌ Server error - this is likely the issue")
            error_detail = response.json().get('detail', 'Unknown error')
            print(f"   Error detail: {error_detail}")
            
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 4: Check if we can access the sheets list
    print("\n4. Testing sheets list endpoint:")
    
    try:
        response = client.get("/api/google-sheets/")
        print(f"   Status: {response.status_code}")
        if response.status_code == 401:
            print("   ✅ Authentication required (expected)")
        elif response.status_code == 200:
            print("   ✅ List endpoint works")
        else:
            print(f"   Response: {response.json()}")
            
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n" + "=" * 50)
    print("📋 Debug Summary:")
    print("   If you see 500 errors, check the backend logs")
    print("   The most common issues are:")
    print("   1. Database connection problems")
    print("   2. Foreign key constraint violations")
    print("   3. Enum handling issues")
    print("   4. Transaction rollback errors")
    
    print("\n🔧 Next steps:")
    print("   1. Check backend logs for detailed error messages")
    print("   2. Verify database connectivity")
    print("   3. Test with a real sheet ID from the database")
    print("   4. Ensure all migrations are applied")

if __name__ == "__main__":
    debug_delete_sheet()
