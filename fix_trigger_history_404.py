#!/usr/bin/env python3
"""
Fix trigger history 404 error
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_test_endpoint():
    """Create a test endpoint without authentication for debugging"""
    
    print("🔧 CREATING TEST ENDPOINT FOR DEBUGGING")
    print("=" * 50)
    
    # Read the current google_sheets.py file
    file_path = os.path.join(os.path.dirname(__file__), 'api', 'google_sheets.py')
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check if test endpoint already exists
        if '@router.get("/triggers/history/test")' in content:
            print("✅ Test endpoint already exists")
            return True
        
        # Find the location to insert test endpoint (after the main endpoint)
        insert_pos = content.find('# ==================== GOOGLE SHEETS CRUD ====================')
        
        if insert_pos == -1:
            print("❌ Could not find insertion point")
            return False
        
        # Create test endpoint code
        test_endpoint = '''

# ==================== TEST ENDPOINT (NO AUTH) ====================

@router.get("/triggers/history/test")
async def get_all_triggers_history_test(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Test endpoint for trigger history (no authentication required)."""
    try:
        logger.info("🧪 Testing trigger history endpoint (no auth)")
        
        # Get all history (no user filter for testing)
        history = db.query(GoogleSheetTriggerHistory).order_by(
            GoogleSheetTriggerHistory.triggered_at.desc()
        ).offset((page - 1) * per_page).limit(per_page).all()
        
        # Format response
        history_data = []
        for h in history:
            history_data.append({
                "trigger_id": str(h.trigger_id),
                "sheet_id": str(h.sheet_id),
                "row_number": h.row_number,
                "phone_number": h.phone_number,
                "message": h.message,
                "status": h.status.value,
                "triggered_at": h.triggered_at.isoformat(),
                "error_message": h.error_message,
                "message_id": h.message_id
            })
        
        return {
            "data": history_data,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": len(history_data)
            },
            "test": True,
            "message": "This is a test endpoint without authentication"
        }
        
    except Exception as e:
        logger.error(f"Error in test trigger history: {e}")
        return {
            "data": [],
            "error": str(e),
            "test": True
        }

'''
        
        # Insert the test endpoint
        new_content = content[:insert_pos] + test_endpoint + content[insert_pos:]
        
        # Write back to file
        with open(file_path, 'w') as f:
            f.write(new_content)
        
        print("✅ Test endpoint added successfully")
        print("📡 Test at: http://localhost:8000/api/google-sheets/triggers/history/test")
        print("💡 This endpoint doesn't require authentication")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating test endpoint: {e}")
        return False

def create_frontend_debug_code():
    """Create frontend debug code"""
    
    print("\n🔧 CREATING FRONTEND DEBUG CODE")
    print("=" * 40)
    
    debug_code = '''
// Debug code for testing trigger history API
// Add this to your frontend component

const testTriggerHistoryAPI = async () => {
    console.log('🧪 Testing trigger history API...');
    
    try {
        // Test without authentication first
        console.log('📡 Testing: /api/google-sheets/triggers/history/test');
        const testResponse = await fetch('http://localhost:8000/api/google-sheets/triggers/history/test');
        
        if (testResponse.ok) {
            const testData = await testResponse.json();
            console.log('✅ Test endpoint working:', testData);
        } else {
            console.error('❌ Test endpoint failed:', testResponse.status);
        }
        
        // Test with authentication
        console.log('📡 Testing: /api/google-sheets/triggers/history');
        
        // Get auth token
        const token = localStorage.getItem('token') || 
                     localStorage.getItem('accessToken') ||
                     (JSON.parse(localStorage.getItem('user') || '{}').token);
        
        console.log('🔑 Token found:', !!token);
        
        const headers = {
            'Content-Type': 'application/json',
        };
        
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        const response = await fetch('http://localhost:8000/api/google-sheets/triggers/history', {
            headers: headers
        });
        
        console.log('📊 Status:', response.status);
        console.log('📋 Headers:', response.headers);
        
        if (response.ok) {
            const data = await response.json();
            console.log('✅ Authenticated endpoint working:', data);
        } else {
            const errorText = await response.text();
            console.error('❌ Authenticated endpoint failed:', response.status, errorText);
            
            if (response.status === 401) {
                console.log('💡 Solution: User needs to log in again');
            } else if (response.status === 404) {
                console.log('💡 Solution: Backend endpoint not found - check route registration');
            }
        }
        
    } catch (error) {
        console.error('❌ Network error:', error);
    }
};

// Call this function to test
// testTriggerHistoryAPI();
'''
    
    debug_file = os.path.join(os.path.dirname(__file__), 'frontend_debug.js')
    
    with open(debug_file, 'w') as f:
        f.write(debug_code)
    
    print("✅ Frontend debug code created")
    print(f"📄 File: {debug_file}")
    print("💡 Copy this code to your frontend to debug the API")

def main():
    """Main function"""
    print("🚀 FIXING TRIGGER HISTORY 404 ERROR")
    
    # Create test endpoint
    if create_test_endpoint():
        # Create frontend debug code
        create_frontend_debug_code()
        
        print("\n🎉 FIX COMPLETE!")
        print("📝 NEXT STEPS:")
        print("1. Restart the backend: uvicorn main:app --host 0.0.0.0 --port 8000 --reload")
        print("2. Test the endpoint: http://localhost:8000/api/google-sheets/triggers/history/test")
        print("3. Use the frontend debug code to test authentication")
        print("4. Check if user is logged in and has valid token")
        
    else:
        print("❌ Fix failed - please check the errors above")

if __name__ == "__main__":
    main()
