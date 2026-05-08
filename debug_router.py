#!/usr/bin/env python3
"""
Debug the router object
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def debug_router():
    """Debug the router object"""
    
    print("🔍 DEBUGGING GOOGLE SHEETS ROUTER")
    print("=" * 40)
    
    try:
        from api.google_sheets import router
        
        print(f"📊 Router type: {type(router)}")
        print(f"📊 Router name: {getattr(router, 'name', 'No name')}")
        
        # Check if it's an APIRouter
        from fastapi import APIRouter
        print(f"📊 Is APIRouter: {isinstance(router, APIRouter)}")
        
        # Check routes
        if hasattr(router, 'routes'):
            print(f"📊 Routes attribute exists: {router.routes}")
            print(f"📊 Routes type: {type(router.routes)}")
            print(f"📊 Routes length: {len(router.routes)}")
            
            # Print first few routes
            for i, route in enumerate(router.routes[:5]):
                print(f"   Route {i}: {type(route)} - {getattr(route, 'path', 'No path')}")
        else:
            print("❌ No routes attribute")
        
        # Check if router is properly initialized
        print(f"📊 Router prefix: {getattr(router, 'prefix', 'No prefix')}")
        print(f"📊 Router tags: {getattr(router, 'tags', 'No tags')}")
        
        return router
        
    except Exception as e:
        print(f"❌ Error debugging router: {e}")
        return None

def test_router_directly():
    """Test router directly"""
    
    print("\n🧪 TESTING ROUTER DIRECTLY")
    print("=" * 30)
    
    try:
        from api.google_sheets import router
        from fastapi import FastAPI
        
        # Create test app
        app = FastAPI()
        
        # Add router
        app.include_router(router, prefix="/api/google-sheets")
        
        # Check app routes
        print(f"📊 App routes after include: {len(app.routes)}")
        
        for route in app.routes:
            if hasattr(route, 'path'):
                print(f"   📍 {getattr(route, 'methods', 'No methods')} {route.path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing router: {e}")
        return False

def main():
    """Main function"""
    print("🚀 ROUTER DEBUG")
    
    # Debug router
    router = debug_router()
    
    # Test router
    if router:
        test_router_directly()

if __name__ == "__main__":
    main()
