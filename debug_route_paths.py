#!/usr/bin/env python3
"""
Debug route paths in detail
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

def debug_route_paths():
    """Debug route paths in detail"""
    
    print("🔍 DEBUGGING ROUTE PATHS")
    print("=" * 40)
    
    try:
        from fastapi import FastAPI
        from api import google_sheets_router
        
        # Create app and include router
        app = FastAPI()
        app.include_router(google_sheets_router, prefix="/api")
        
        print(f"📊 Total routes: {len(app.routes)}")
        
        # Examine each route in detail
        for i, route in enumerate(app.routes):
            print(f"\n📍 Route {i}:")
            print(f"   Type: {type(route)}")
            
            if hasattr(route, 'path'):
                print(f"   Path: {route.path}")
                print(f"   Methods: {getattr(route, 'methods', 'No methods')}")
                print(f"   Name: {getattr(route, 'name', 'No name')}")
            
            if hasattr(route, 'path_prefix'):
                print(f"   Path Prefix: {route.path_prefix}")
                print(f"   Is Router: {hasattr(route, 'routes')}")
                
                if hasattr(route, 'routes'):
                    print(f"   Sub-routes: {len(route.routes)}")
                    for j, sub_route in enumerate(route.routes[:3]):  # Show first 3
                        print(f"      Sub-route {j}: {sub_route.path}")
                        if hasattr(sub_route, 'methods'):
                            print(f"         Methods: {sub_route.methods}")
            
            # Check if this is a Google Sheets route
            route_path = getattr(route, 'path', '')
            route_prefix = getattr(route, 'path_prefix', '')
            
            if 'google-sheets' in route_path or 'google-sheets' in route_prefix:
                print(f"   ✅ GOOGLE SHEETS ROUTE FOUND!")
            elif hasattr(route, 'routes'):
                # Check sub-routes
                for sub_route in route.routes:
                    if hasattr(sub_route, 'path'):
                        full_path = f"{route.path_prefix}{sub_route.path}"
                        if 'google-sheets' in full_path:
                            print(f"   ✅ GOOGLE SHEETS SUB-ROUTE FOUND: {full_path}")
        
        # Now let's check what's actually in the router
        print(f"\n🔍 ROUTER DIRECT INSPECTION:")
        print(f"Router type: {type(google_sheets_router)}")
        print(f"Router routes: {len(google_sheets_router.routes)}")
        
        for i, route in enumerate(google_sheets_router.routes[:5]):
            print(f"   Router Route {i}: {route.path} - {getattr(route, 'methods', 'No methods')}")
        
        # Check if router has a prefix
        print(f"Router prefix: {getattr(google_sheets_router, 'prefix', 'No prefix')}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def test_with_different_prefix():
    """Test with different prefix"""
    
    print("\n🧪 TESTING WITH DIFFERENT PREFIX")
    print("=" * 45)
    
    try:
        from fastapi import FastAPI
        from api import google_sheets_router
        
        # Test with /api/google-sheets prefix
        app = FastAPI()
        app.include_router(google_sheets_router, prefix="/api/google-sheets")
        
        print(f"📊 Routes with /api/google-sheets prefix: {len(app.routes)}")
        
        # Check routes
        gs_routes = []
        for route in app.routes:
            if hasattr(route, 'path'):
                if 'google-sheets' in route.path:
                    gs_routes.append(route.path)
                    print(f"   ✅ {route.path}")
        
        print(f"📊 Google Sheets routes found: {len(gs_routes)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Main function"""
    print("🚀 ROUTE PATHS DEBUG")
    print("=" * 50)
    
    debug_route_paths()
    test_with_different_prefix()

if __name__ == "__main__":
    main()
