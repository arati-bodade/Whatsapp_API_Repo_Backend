from pydantic import ValidationError
import uuid
import sys
import os

# Add parent directory to path to import schemas
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from schemas.google_sheet import TriggerCreateRequest

def test_trigger_create_request_schema():
    print("Testing TriggerCreateRequest schema...")
    
    # Test case 1: sheet_id is missing (should be valid now)
    payload = {
        "device_id": str(uuid.uuid4()),
        "trigger_type": "new_row",
        "is_enabled": True
    }
    
    try:
        request = TriggerCreateRequest(**payload)
        print("✅ SUCCESS: Schema accepted payload without sheet_id")
        print(f"Parsed invalid sheet_id as: {request.sheet_id}")
    except ValidationError as e:
        print("❌ FAILED: Schema rejected payload without sheet_id")
        print(e)
        sys.exit(1)

    # Test case 2: sheet_id is provided
    payload_with_id = {
        "sheet_id": str(uuid.uuid4()),
        "device_id": str(uuid.uuid4()),
        "trigger_type": "new_row"
    }
    
    try:
        request = TriggerCreateRequest(**payload_with_id)
        print("✅ SUCCESS: Schema accepted payload WITH sheet_id")
    except ValidationError as e:
        print("❌ FAILED: Schema rejected valid payload")
        print(e)
        sys.exit(1)

if __name__ == "__main__":
    test_trigger_create_request_schema()
