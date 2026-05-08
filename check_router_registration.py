#!/usr/bin/env python3
"""
Check if Google Sheets router is properly registered
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_router_registration():
    """Check router registration"""
    
    print("🔍 CHECKING GOOGLE SHEETS ROUTER REGISTRATION")
    print("=" * 50)
    
    try:
        # Import the router
        from api.google_sheets import router
        print("✅ Google Sheets router imported successfully")
        
        # Check routes
        routes = router.routes
        print(f"📊 Found {len(routes)} routes in Google Sheets router")
        
        for route in routes:
            if hasattr(route, 'path'):
                print(f"   📍 {route.methods} {route.path}")
        
        # Check specific routes
        route_paths = [route.path for route in routes if hasattr(route, 'path')]
        
        expected_routes = [
            "/",
            "/triggers/history/test", 
            "/triggers/history"
        ]
        
        print("\n🔍 CHECKING SPECIFIC ROUTES:")
        for expected in expected_routes:
            if expected in route_paths:
                print(f"   ✅ {expected} - Found")
            else:
                print(f"   ❌ {expected} - Missing")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking router: {e}")
        return False

def check_app_registration():
    """Check if router is registered in app"""
    
    print("\n🔍 CHECKING APP REGISTRATION")
    print("=" * 30)
    
    try:
        from main import app
        
        # Get all routes from app
        app_routes = []
        for route in app.routes:
            if hasattr(route, 'routes'):
                # This is a router, get its routes
                for sub_route in route.routes:
                    if hasattr(sub_route, 'path'):
                        app_routes.append(f"{route.path_prefix}{sub_route.path}")
            elif hasattr(route, 'path'):
                app_routes.append(route.path)
        
        print(f"📊 Total app routes: {len(app_routes)}")
        
        # Check for Google Sheets routes
        gs_routes = [r for r in app_routes if 'google-sheets' in r]
        print(f"📊 Google Sheets routes: {len(gs_routes)}")
        
        for route in gs_routes:
            print(f"   📍 {route}")
        
        # Check specific endpoints
        expected_endpoints = [
            "/api/google-sheets/",
            "/api/google-sheets/triggers/history/test",
            "/api/google-sheets/triggers/history"
        ]
        
        print("\n🔍 CHECKING SPECIFIC ENDPOINTS:")
        for expected in expected_endpoints:
            if expected in app_routes:
                print(f"   ✅ {expected} - Found")
            else:
                print(f"   ❌ {expected} - Missing")
        
        return len(gs_routes) > 0
        
    except Exception as e:
        print(f"❌ Error checking app: {e}")
        return False

def main():
    """Main function"""
    print("🚀 ROUTER REGISTRATION CHECK")
    
    # Check router
    router_ok = check_router_registration()
    
    # Check app registration
    app_ok = check_app_registration()
    
    print("\n" + "=" * 50)
    print("📋 SUMMARY:")
    
    if router_ok and app_ok:
        print("✅ Router is properly registered")
        print("✅ Endpoints should be accessible")
        print("\n💡 If endpoints still return 404:")
        print("   1. Backend might be hanging during startup")
        print("   2. Database connection issues")
        print("   3. Check backend startup logs")
    else:
        print("❌ Router registration issues found")
        print("💡 Check import errors or missing dependencies")

if __name__ == "__main__":
    main()
