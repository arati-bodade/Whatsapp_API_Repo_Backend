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
