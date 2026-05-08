#!/usr/bin/env python3
"""
Production Deployment Script for WhatsApp Platform Backend
"""

import os
import sys
import subprocess
import time

def check_dependencies():
    """Check if all required dependencies are installed."""
    required_packages = [
        ('fastapi', 'fastapi'),
        ('uvicorn', 'uvicorn'),
        ('sqlalchemy', 'sqlalchemy'),
        ('psycopg2-binary', 'psycopg2'),
        ('pydantic', 'pydantic'),
        ('python-dotenv', 'python-dotenv')
    ]
    
    missing_packages = []
    
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
            print(f"✅ {package_name} - Available")
        except ImportError:
            missing_packages.append(package_name)
            print(f"❌ {package_name} - Missing")
    
    if missing_packages:
        print(f"\n❌ Missing dependencies: {', '.join(missing_packages)}")
        print("Please install missing packages:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True

def check_database():
    """Check database connection."""
    try:
        from db.base import engine
        from sqlalchemy import text
        
        conn = engine.connect()
        result = conn.execute(text('SELECT 1'))
        conn.close()
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def start_production_server():
    """Start the production server."""
    print("\\n🚀 Starting WhatsApp Platform Backend...")
    print("📍 Server: http://127.0.0.1:8000")
    print("📚 API Docs: http://127.0.0.1:8000/docs")
    print("🔍 Health Check: http://127.0.0.1:8000/health")
    
    try:
        # Use uvicorn for production
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "main:app",
            "--host", "127.0.0.1",
            "--port", "8000",
            "--log-level", "info"
        ])
    except KeyboardInterrupt:
        print("\\n\\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\\n❌ Server failed to start: {e}")

def main():
    """Main deployment function."""
    print("=" * 60)
    print("🔍 WHATSAPP PLATFORM BACKEND - DEPLOYMENT CHECK")
    print("=" * 60)
    
    # Check dependencies
    if not check_dependencies():
        print("\\n❌ Cannot proceed with deployment - missing dependencies")
        sys.exit(1)
    
    # Check database
    if not check_database():
        print("\\n❌ Cannot proceed with deployment - database connection failed")
        sys.exit(1)
    
    # Start server
    print("\\n✅ All checks passed - starting production server...")
    start_production_server()

if __name__ == "__main__":
    main()
