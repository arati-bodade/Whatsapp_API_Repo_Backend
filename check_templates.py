#!/usr/bin/env python3
"""
📋 CHECK AVAILABLE TEMPLATES
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.official_message_service import OfficialMessageService
from db.base import SessionLocal

async def check_available_templates():
    """Check what templates are available"""
    print("📋 CHECKING AVAILABLE TEMPLATES...")
    
    db = SessionLocal()
    try:
        # You'll need to replace with actual user ID
        test_user_id = "db6a2832-496d-4efa-922f-003b1a8f2b13"  # Replace with actual user ID
        
        message_service = OfficialMessageService(db)
        templates = await message_service.get_user_templates(test_user_id)
        
        print(f"   Found {len(templates)} approved templates:")
        for template in templates:
            print(f"   📋 {template['template_name']} ({template['language']}) - {template['status']}")
        
        return templates
        
    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
        return None
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(check_available_templates())
