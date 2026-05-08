#!/usr/bin/env python3
"""
Fix existing triggers that still have "[Media Message]" template
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db.session import get_db
from models.google_sheet import GoogleSheetTrigger
import json

def fix_old_triggers():
    """Update triggers with old '[Media Message]' template to empty string"""
    
    print("=== Fixing Old Trigger Templates ===")
    
    # Get database session
    db = next(get_db())
    
    try:
        # Get all triggers with media
        triggers = db.query(GoogleSheetTrigger).filter(
            GoogleSheetTrigger.media_url.isnot(None)
        ).all()
        
        print(f"Found {len(triggers)} triggers with media:")
        
        updated_count = 0
        for trigger in triggers:
            print(f"\nTrigger ID: {trigger.trigger_id}")
            print(f"Name: {trigger.trigger_name or 'No name'}")
            
            # Parse trigger config
            if trigger.trigger_config:
                try:
                    config = json.loads(trigger.trigger_config) if isinstance(trigger.trigger_config, str) else trigger.trigger_config
                    multi_templates = config.get('multi_templates', [])
                    print(f"Current templates: {multi_templates}")
                    
                    # Check if any template is "[Media Message]"
                    if "[Media Message]" in multi_templates:
                        # Replace with empty string
                        new_templates = ["" if t == "[Media Message]" else t for t in multi_templates]
                        config['multi_templates'] = new_templates
                        
                        # Update the trigger config
                        trigger.trigger_config = json.dumps(config)
                        db.commit()
                        
                        print(f"  Updated templates: {new_templates}")
                        updated_count += 1
                    else:
                        print("  No '[Media Message]' template found")
                        
                except Exception as e:
                    print(f"Error parsing config: {e}")
            else:
                print("No trigger config found")
                
        print(f"\n=== SUMMARY ===")
        print(f"Updated {updated_count} triggers")
        print(f"Fixed '[Media Message]' -> '' (empty string)")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    fix_old_triggers()
