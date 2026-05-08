#!/usr/bin/env python3
"""
Add new media types to the database MessageType enum
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db.session import get_db
from sqlalchemy import text

def add_media_types():
    """Add new media types to MessageType enum"""
    
    print("=== Adding Media Types to Database ===")
    
    # Get database session
    db = next(get_db())
    
    try:
        # Add new media types to the enum
        migrations = [
            ("ALTER TYPE messagetype ADD VALUE 'IMAGE'", "Add IMAGE media type"),
            ("ALTER TYPE messagetype ADD VALUE 'VIDEO'", "Add VIDEO media type"),
            ("ALTER TYPE messagetype ADD VALUE 'AUDIO'", "Add AUDIO media type"),
            ("ALTER TYPE messagetype ADD VALUE 'DOCUMENT'", "Add DOCUMENT media type"),
        ]
        
        for sql, desc in migrations:
            try:
                print(f"   ➕ {desc}...")
                db.execute(text(sql))
                db.commit()
                print(f"   ✅ {desc} added successfully")
            except Exception as e:
                if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                    print(f"   ⚠️ {desc} already exists - skipping")
                else:
                    print(f"   ❌ {desc} failed: {str(e)}")
                    
        print("\n✅ Media types migration completed!")
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    add_media_types()
