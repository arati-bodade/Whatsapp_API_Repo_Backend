#!/usr/bin/env python3
"""
Debug exactly what caption is being sent
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db.session import get_db
from services.unified_service import UnifiedWhatsAppService
from schemas.unified import UnifiedMessageRequest, MessageType
import re

def debug_caption_issue():
    """Debug exactly what caption is being sent to engine"""
    
    print("=== Debugging Caption Issue ===")
    
    # Get database session
    db = next(get_db())
    
    try:
        # Test filename cleaning directly
        print("1. Testing filename cleaning...")
        test_file = "trigger_33496d04-29aa-4770-a9f3-4c7294ed5746.jpg"
        
        # New logic: Handle both formats
        if re.match(r'^trigger_[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.', test_file):
            # Format: trigger_UUID.ext -> .ext (just the extension)
            clean_name = re.sub(r'^trigger_[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '', test_file)
        elif re.match(r'^trigger_[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}_', test_file):
            # Format: trigger_UUID_name.ext -> name.ext
            clean_name = re.sub(r'^trigger_[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}_', '', test_file)
        else:
            clean_name = test_file
            
        print(f"   Original: {test_file}")
        print(f"   Cleaned:  {clean_name}")
        
        # Test what happens in engine service
        print("\n2. Testing engine service behavior...")
        from services.whatsapp_engine_service import WhatsAppEngineService
        engine_service = WhatsAppEngineService()
        
        # Simulate the exact flow
        file_path = "uploads/trigger_media/trigger_33496d04-29aa-4770-a9f3-4c7294ed5746.jpg"
        caption = ""  # Empty for media-only
        
        print(f"   File path: {file_path}")
        print(f"   Input caption: '{caption}'")
        
        # Check if file is local
        is_local = not file_path.startswith('http') and (file_path.startswith('/') or os.path.exists(file_path))
        print(f"   Is local: {is_local}")
        
        if is_local and os.path.exists(file_path):
            print("   Using local file logic...")
            # Simulate the local file logic
            raw_filename = os.path.basename(file_path)
            
            # New logic: Handle both formats
            if re.match(r'^trigger_[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.', raw_filename):
                # Format: trigger_UUID.ext -> .ext (just the extension)
                filename = re.sub(r'^trigger_[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '', raw_filename)
            elif re.match(r'^trigger_[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}_', raw_filename):
                # Format: trigger_UUID_name.ext -> name.ext
                filename = re.sub(r'^trigger_[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}_', '', raw_filename)
            else:
                filename = raw_filename
                
            print(f"   Raw filename: {raw_filename}")
            print(f"   Clean filename: {filename}")
            
            # Check caption logic
            user_caption = caption
            if user_caption:
                user_caption = user_caption.replace(raw_filename, filename)
                print(f"   User caption after replace: '{user_caption}'")
            else:
                print(f"   User caption is empty: '{user_caption}'")
            
            # Check final caption logic
            final_caption = user_caption if user_caption is not None else filename
            print(f"   Final caption: '{final_caption}'")
        
        # Test unified service directly
        print("\n3. Testing unified service...")
        unified_service = UnifiedWhatsAppService(db)
        
        test_request = UnifiedMessageRequest(
            to="+919876543210",
            type=MessageType.IMAGE,
            message="",  # Empty for media-only
            media_url="http://localhost:8000/uploads/trigger_media/trigger_33496d04-29aa-4770-a9f3-4c7294ed5746.jpg",
            device_id="e0266dcb-d968-4180-988f-9542c77bfc1a",
            user_id="e74e56ab-4d68-4fcd-bef7-2f7ea64ab6d2"
        )
        
        # Check what message body gets built
        message_body = unified_service._build_message_body(test_request)
        print(f"   Message body built: '{message_body}'")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    debug_caption_issue()
