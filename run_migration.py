#!/usr/bin/env python3
"""
Script to run the UUID migration safely
"""
import os
import sys
from dotenv import load_dotenv

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

def main():
    print("🚀 Starting google_sheet_triggers.sheet_id UUID migration...")
    
    # Check DATABASE_URL
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        return False
    
    print(f"📡 Database URL: {database_url.split('@')[1] if '@' in database_url else 'local'}")
    
    # Run migration using alembic
    import subprocess
    try:
        result = subprocess.run([
            'alembic', 'upgrade', 'head'
        ], capture_output=True, text=True, cwd=os.path.dirname(os.path.abspath(__file__)))
        
        if result.returncode == 0:
            print("✅ Migration completed successfully!")
            print(result.stdout)
            return True
        else:
            print("❌ Migration failed!")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error running migration: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
