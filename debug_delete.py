#!/usr/bin/env python3

import requests
import uuid
import json

def test_delete_endpoint():
    """Test the delete endpoint directly"""
    
    # Test data
    test_group_id = str(uuid.uuid4())
    test_contact_id = str(uuid.uuid4())
    
    url = f"http://localhost:3000/api/groups/{test_group_id}/contacts"
    payload = {"contact_id": test_contact_id}
    
    print(f"Testing DELETE endpoint: {url}")
    print(f"Payload: {payload}")
    
    try:
        response = requests.delete(url, json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except requests.exceptions.ConnectionError:
        print("Connection refused - backend server not running on localhost:3000")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_delete_endpoint()
