#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from main import app
import uuid

# Create test client
client = TestClient(app)

def test_delete_sheet_debug():
    """Test the delete sheet endpoint with debugging"""
    
    # Test with a fake sheet ID to see the exact error
    test_sheet_id = str(uuid.uuid4())
    
    print(f"Testing DELETE sheet with ID: {test_sheet_id}")
    
    response = client.delete(f"/api/google-sheets/{test_sheet_id}")
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"Response Data: {response.json()}")
    
    # Also test the list endpoint to make sure basic API works
    print("\n" + "="*50)
    print("Testing GET /google-sheets/ to verify API is working:")
    
    list_response = client.get("/api/google-sheets/")
    print(f"List Status: {list_response.status_code}")
    if list_response.status_code != 200:
        print(f"List Response: {list_response.json()}")

if __name__ == "__main__":
    test_delete_sheet_debug()
