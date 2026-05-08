#!/usr/bin/env python3
"""
Debug the manual send 422 error by adding logging to the endpoint
"""

from fastapi import Request
from fastapi.testclient import TestClient
from main import app
import json

# Add debugging middleware to capture the exact request
@app.middleware("http")
async def debug_manual_send_requests(request: Request, call_next):
    if "/manual-send" in str(request.url):
        print(f"\n🔍 Manual Send Request Debug:")
        print(f"URL: {request.url}")
        print(f"Method: {request.method}")
        print(f"Headers: {dict(request.headers)}")
        
        try:
            body = await request.body()
            print(f"Body: {body.decode('utf-8')}")
        except Exception as e:
            print(f"Error reading body: {e}")
    
    response = await call_next(request)
    return response

def test_with_auth():
    """Test with simulated auth to see 422 error"""
    client = TestClient(app)
    
    sheet_id = 'e97846dd-62f0-407b-9ad9-417463d5f1d1'
    
    # Try different payload variations that might cause 422
    payloads = [
        # Standard payload
        {
            'device_id': '4337c1ea-29fe-4673-b7bd-0c4bffca4ec5',
            'message_template': 'Hello {name}',
            'phone_column': 'A',
            'send_all': True
        },
        # Missing phone_column
        {
            'device_id': '4337c1ea-29fe-4673-b7bd-0c4bffca4ec5',
            'message_template': 'Hello {name}',
            'send_all': True
        },
        # Invalid device_id format
        {
            'device_id': 'invalid-device-id',
            'message_template': 'Hello {name}',
            'phone_column': 'A',
            'send_all': True
        },
        # Empty message template
        {
            'device_id': '4337c1ea-29fe-4673-b7bd-0c4bffca4ec5',
            'message_template': '',
            'phone_column': 'A',
            'send_all': True
        }
    ]
    
    for i, payload in enumerate(payloads):
        print(f"\n🧪 Test {i+1}:")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        try:
            response = client.post(f'/api/google-sheets/{sheet_id}/manual-send', json=payload)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 422:
                print("❌ 422 Error Details:")
                print(json.dumps(response.json(), indent=2))
            elif response.status_code == 401:
                print("✅ Auth required (expected)")
            else:
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    print("🔍 Debugging Manual Send 422 Error")
    print("=" * 50)
    test_with_auth()
