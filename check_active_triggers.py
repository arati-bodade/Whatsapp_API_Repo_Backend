#!/usr/bin/env python3
"""
Check all triggers (enabled and disabled) for old templates
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db.session import get_db
from models.google_sheet import GoogleSheetTrigger
import json

def check_all_triggers():
    """Check all triggers for old '[Media Message]' templates"""
    
    print("=== Checking All Triggers for Old Templates ===")
    
    # Get database session
    db = next(get_db())
    
    try:
        # Get ALL triggers (not just enabled ones)
        triggers = db.query(GoogleSheetTrigger).all()
        
        print(f"Found {len(triggers)} total triggers:")
        
        for trigger in triggers:
            print(f"\nTrigger ID: {trigger.trigger_id}")
            print(f"Name: {trigger.trigger_name or 'No name'}")
            print(f"Enabled: {trigger.is_enabled}")
            print(f"Media URL: {trigger.media_url}")
            print(f"Media Type: {trigger.media_type}")
            
            # Parse trigger config
            if trigger.trigger_config:
                try:
                    config = json.loads(trigger.trigger_config) if isinstance(trigger.trigger_config, str) else trigger.trigger_config
                    multi_templates = config.get('multi_templates', [])
                    print(f"Templates: {multi_templates}")
                    
                    # Check for old template
                    if "[Media Message]" in multi_templates:
                        print("  ** FOUND OLD '[Media Message]' TEMPLATE! **")
                    elif "" in multi_templates:
                        print("  ** Has empty template (our fix) **")
                    else:
                        print("  ** Has regular text templates **")
                        
                except Exception as e:
                    print(f"Error parsing config: {e}")
            else:
                print("No trigger config found")
                
        if not triggers:
            print("No triggers found in database")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_all_triggers()
