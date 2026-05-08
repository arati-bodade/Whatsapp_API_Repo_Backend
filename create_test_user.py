#!/usr/bin/env python3

import requests
import json
import uuid

# Configuration
BASE_URL = "http://127.0.0.1:8000"

def create_test_business_user():
    """Create a test business user for testing"""
    
    # First, we need a reseller to create a business user
    # Let's try to create a reseller first
    reseller_data = {
        "profile": {
            "name": "API Test Reseller",
            "username": "apitestreseller",
            "email": "apitest@reseller.com",
            "phone": "+1234567899",
            "password": "testpass123"
        },
        "business": {
            "business_name": "API Test Company"
        },
        "address": {
            "full_address": "API Test Address",
            "pincode": "12345",
            "country": "Test Country"
        }
    }
    
    try:
        # Login with existing reseller
        login_data = {"email": "apitest@reseller.com", "password": "testpass123"}
        response = requests.post(f"{BASE_URL}/api/resellers/login", json=login_data)
        if response.status_code == 200:
            reseller = response.json()
            reseller_id = reseller['reseller_id']
            print(f"✅ Logged in reseller: {reseller_id}")
        else:
            print(f"❌ Failed to login reseller: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error logging in reseller: {e}")
        return None
    
    # Now create a business user
    business_data = {
        "parent_reseller_id": reseller_id,
        "profile": {
            "name": "Test Business User",
            "username": "testbusiness",
            "email": "test@business.com",
            "phone": "+1234567891",
            "password": "testpass123"
        },
        "business": {
            "business_name": "Test Business",
            "business_description": "Test business for API testing"
        },
        "wallet": {
            "credits_allocated": 100
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/busi_users/register", json=business_data)
        if response.status_code == 200:
            business = response.json()
            print(f"✅ Created business user: {business['busi_user_id']}")
            return business
        else:
            print(f"❌ Failed to create business user: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error creating business user: {e}")
        return None

def login_business_user():
    """Login as business user and get token"""
    login_data = {
        "email": "test@business.com",
        "password": "testpass123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/busi_users/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Business user login successful!")
            print(f"   Token: {data['access_token'][:50]}...")
            print(f"   User ID: {data['busi_user']['busi_user_id']}")
            return data['access_token']
        else:
            print(f"❌ Business user login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error logging in business user: {e}")
        return None

def test_google_sheets_with_token(token):
    """Test Google Sheets API with valid token"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/api/google-sheets/", headers=headers)
        print(f"🔍 Google Sheets API test: {response.status_code}")
        if response.status_code == 200:
            sheets = response.json()
            print(f"✅ Google Sheets API working! Found {len(sheets)} sheets")
            for sheet in sheets:
                print(f"   - {sheet['sheet_name']} ({sheet['status']})")
        else:
            print(f"❌ Google Sheets API error: {response.text}")
    except Exception as e:
        print(f"❌ Error testing Google Sheets API: {e}")

def test_templates_with_token(token):
    """Test Templates API with valid token"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/api/official-whatsapp/config/templates", headers=headers)
        print(f"🔍 Templates API test: {response.status_code}")
        if response.status_code == 200:
            templates = response.json()
            print(f"✅ Templates API working! Found {len(templates)} templates")
            for template in templates:
                print(f"   - {template['template_name']} ({template['template_status']})")
        else:
            print(f"❌ Templates API error: {response.text}")
    except Exception as e:
        print(f"❌ Error testing Templates API: {e}")

if __name__ == "__main__":
    print("Creating Test User and Testing APIs...")
    print("=" * 50)
    
    # Create test business user
    business_user = create_test_business_user()
    
    if business_user:
        print("\nTesting login...")
        token = login_business_user()
        
        if token:
            print("\nTesting APIs with valid token...")
            test_google_sheets_with_token(token)
            test_templates_with_token(token)
        else:
            print("❌ Cannot test APIs without valid token")
    else:
        print("❌ Cannot test APIs without business user")
    
    print("\n" + "=" * 50)
    print("Test complete!")
