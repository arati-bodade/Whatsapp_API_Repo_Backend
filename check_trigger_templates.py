#!/usr/bin/env python3
"""
Check what templates are stored in active triggers
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db.session import get_db
from models.google_sheet import GoogleSheetTrigger
import json

def check_trigger_templates():
    """Check templates in active triggers"""
    
    print("=== Checking Trigger Templates ===")
    
    # Get database session
    db = next(get_db())
    
    try:
        # Get all active triggers
        triggers = db.query(GoogleSheetTrigger).filter(GoogleSheetTrigger.is_enabled == True).all()
        
        print(f"Found {len(triggers)} active triggers:")
        
        for trigger in triggers:
            print(f"\nTrigger ID: {trigger.trigger_id}")
            print(f"Name: {trigger.trigger_name or 'No name'}")
            print(f"Media URL: {trigger.media_url}")
            print(f"Media Type: {trigger.media_type}")
            
            # Parse trigger config
            if trigger.trigger_config:
                try:
                    config = json.loads(trigger.trigger_config) if isinstance(trigger.trigger_config, str) else trigger.trigger_config
                    multi_templates = config.get('multi_templates', [])
                    print(f"Templates: {multi_templates}")
                    
                    # Check if any template is "[Media Message]"
                    if "[Media Message]" in multi_templates:
                        print("⚠️  FOUND OLD '[Media Message]' TEMPLATE!")
                    # Check if any template is empty (our fix)
                    if "" in multi_templates:
                        print("✅ FOUND EMPTY TEMPLATE (our fix)")
                        
                except Exception as e:
                    print(f"Error parsing config: {e}")
            else:
                print("No trigger config found")
                
        if not triggers:
            print("No active triggers found")
            
    except Exception as e:
        print(f"❌ Error checking triggers: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_trigger_templates()
