#!/usr/bin/env python3
"""
Debug the exact message flow for media-only triggers
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db.session import get_db
from services.unified_service import UnifiedWhatsAppService
from schemas.unified import UnifiedMessageRequest, MessageType

def debug_media_flow():
    """Debug exactly what message is sent to engine"""
    
    print("=== Debugging Media-Only Message Flow ===")
    
    # Get database session
    db = next(get_db())
    
    try:
        unified_service = UnifiedWhatsAppService(db)
        
        # Create media-only request
        test_request = UnifiedMessageRequest(
            to="+919876543210",
            type=MessageType.IMAGE,
            message="",  # Empty message for media-only
            media_url="http://localhost:8000/uploads/trigger_media/trigger_33496d04-29aa-4770-a9f3-4c7294ed5746.jpg",
            device_id="e0266dcb-d968-4180-988f-9542c77bfc1a",
            user_id="e74e56ab-4d68-4fcd-bef7-2f7ea64ab6d2"
        )
        
        print(f"Input request:")
        print(f"  - Message: '{test_request.message}'")
        print(f"  - Media URL: {test_request.media_url}")
        print(f"  - Type: {test_request.type}")
        
        # Add debug logging to see what gets sent to engine
        print("\nCalling unified service...")
        
        # Let's manually trace what happens in the unified service
        from services.whatsapp_engine_service import WhatsAppEngineService
        engine_service = WhatsAppEngineService()
        
        # Convert URL to local path (as done in unified service)
        media_path = test_request.media_url
        if media_path.startswith('http://localhost:8000/uploads/'):
            media_path = media_path.replace('http://localhost:8000/uploads/', 'uploads/')
        elif media_path.startswith('http://127.0.0.1:8000/uploads/'):
            media_path = media_path.replace('http://127.0.0.1:8000/uploads/', 'uploads/')
        
        print(f"Converted media path: '{media_path}'")
        
        # Check what caption would be sent to engine
        caption = test_request.message  # This should be empty
        print(f"Caption to send to engine: '{caption}'")
        
        # Test engine service directly
        print("\nCalling engine service directly...")
        result = engine_service.send_file_with_caption(
            device_id=str(test_request.device_id),
            to=test_request.to,
            file_path=media_path,
            caption=caption,
            device_name="Debug Test"
        )
        
        print(f"Engine service result: {result}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    debug_media_flow()
