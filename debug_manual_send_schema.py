#!/usr/bin/env python3
"""
Debug manual send schema mismatch
"""

from pydantic import ValidationError
from schemas.google_sheet import ManualSendRequest
import json

def test_manual_send_schema():
    """Test various payload formats against the schema"""
    
    print("🔍 Testing Manual Send Schema Validation")
    print("=" * 60)
    
    # Test cases that frontend might send
    test_cases = [
        {
            "name": "Standard payload (frontend likely sends)",
            "payload": {
                "device_id": "4337c1ea-29fe-4673-b7bd-0c4bffca4ec5",
                "message_template": "Hello {name}",
                "phone_column": "A",
                "send_all": True
            }
        },
        {
            "name": "With selected_rows",
            "payload": {
                "device_id": "4337c1ea-29fe-4673-b7bd-0c4bffca4ec5",
                "message_template": "Hello {name}",
                "phone_column": "A",
                "send_all": False,
                "selected_rows": [{"name": "John", "phone": "+1234567890"}]
            }
        },
        {
            "name": "Missing send_all (default False)",
            "payload": {
                "device_id": "4337c1ea-29fe-4673-b7bd-0c4bffca4ec5",
                "message_template": "Hello {name}",
                "phone_column": "A"
            }
        },
        {
            "name": "Empty message template",
            "payload": {
                "device_id": "4337c1ea-29fe-4673-b7bd-0c4bffca4ec5",
                "message_template": "",
                "phone_column": "A",
                "send_all": True
            }
        },
        {
            "name": "Empty phone column",
            "payload": {
                "device_id": "4337c1ea-29fe-4673-b7bd-0c4bffca4ec5",
                "message_template": "Hello {name}",
                "phone_column": "",
                "send_all": True
            }
        },
        {
            "name": "Invalid device_id format",
            "payload": {
                "device_id": "invalid-device-id",
                "message_template": "Hello {name}",
                "phone_column": "A",
                "send_all": True
            }
        },
        {
            "name": "String device_id (not UUID)",
            "payload": {
                "device_id": "1",
                "message_template": "Hello {name}",
                "phone_column": "A",
                "send_all": True
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {test_case['name']}")
        print(f"   Payload: {json.dumps(test_case['payload'], indent=4)}")
        
        try:
            # Test schema validation
            request = ManualSendRequest(**test_case['payload'])
            print(f"   ✅ Schema validation PASSED")
            print(f"   Parsed values:")
            print(f"     device_id: {request.device_id} (type: {type(request.device_id)})")
            print(f"     message_template: '{request.message_template}'")
            print(f"     phone_column: '{request.phone_column}'")
            print(f"     send_all: {request.send_all}")
            print(f"     selected_rows: {request.selected_rows}")
            
        except ValidationError as e:
            print(f"   ❌ Schema validation FAILED")
            print(f"   Error: {e}")
            
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")
    
    print("\n" + "=" * 60)
    print("📋 Schema Analysis Complete")

if __name__ == "__main__":
    test_manual_send_schema()
