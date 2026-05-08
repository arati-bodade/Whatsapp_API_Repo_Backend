// Frontend Login Debug Script
// Run this in browser console to debug login issues

console.log("🔍 Frontend Login Debug Tool");
console.log("=" * 50);

// 1. Check API Configuration
console.log("\n1. API Configuration:");
console.log("API_BASE_URL:", window.location?.origin?.includes('localhost') ? 
    (window.location.origin + "/api") : 
    "https://whatsapp-platfrom-backent1.onrender.com/api");

// 2. Check localStorage
console.log("\n2. Current localStorage state:");
console.log("Token:", localStorage.getItem('token'));
console.log("Refresh Token:", localStorage.getItem('refreshToken'));
console.log("User Role:", localStorage.getItem('user_role'));
console.log("User ID:", localStorage.getItem('user_id'));
console.log("Reseller Token:", localStorage.getItem('resellerToken'));

// 3. Test API connectivity
async function testAPI() {
    console.log("\n3. Testing API connectivity:");
    
    try {
        // Test API root
        const response = await fetch(window.location?.origin?.includes('localhost') ? 
            `${window.location.origin}/api/busi_users/` : 
            "https://whatsapp-platfrom-backent1.onrender.com/api/busi_users/");
        
        console.log("API Status:", response.status);
        
        if (response.ok) {
            const users = await response.json();
            console.log("✅ API is working, found users:", users.length);
        } else {
            console.log("❌ API Error:", response.status);
        }
    } catch (error) {
        console.log("❌ Network Error:", error.message);
    }
}

// 4. Test login endpoint
async function testLogin() {
    console.log("\n4. Testing login endpoint:");
    
    try {
        const loginData = {
            email: "test@example.com",
            password: "testpassword"
        };
        
        const response = await fetch(window.location?.origin?.includes('localhost') ? 
            `${window.location.origin}/api/busi_users/login` : 
            "https://whatsapp-platfrom-backent1.onrender.com/api/busi_users/login", {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(loginData)
        });
        
        console.log("Login Status:", response.status);
        console.log("Login Response:", await response.json());
        
        if (response.status === 200) {
            console.log("✅ Login endpoint working");
        } else if (response.status === 401) {
            console.log("✅ Login endpoint exists (401 for invalid credentials)");
        } else {
            console.log("❌ Login error:", response.status);
        }
    } catch (error) {
        console.log("❌ Login test error:", error.message);
    }
}

// 5. Check form submission
function checkForm() {
    console.log("\n5. Checking login form:");
    
    const loginForm = document.querySelector('form');
    if (loginForm) {
        console.log("✅ Login form found");
        
        const emailInput = document.querySelector('input[type="email"]');
        const passwordInput = document.querySelector('input[type="password"]');
        const submitButton = document.querySelector('button[type="submit"]');
        
        console.log("Email input:", emailInput ? "✅ Found" : "❌ Not found");
        console.log("Password input:", passwordInput ? "✅ Found" : "❌ Not found");
        console.log("Submit button:", submitButton ? "✅ Found" : "❌ Not found");
        
        if (emailInput && passwordInput) {
            console.log("Email value:", emailInput.value);
            console.log("Password value:", passwordInput.value ? "***" : "(empty)");
        }
    } else {
        console.log("❌ Login form not found");
    }
}

// 6. Simulate login process
async function simulateLogin() {
    console.log("\n6. Simulating login process:");
    
    const email = "tushar.nimbolkar@gmail.com"; // Known user from backend
    const password = "password123"; // You'll need to know the actual password
    
    try {
        const response = await fetch(window.location?.origin?.includes('localhost') ? 
            `${window.location.origin}/api/busi_users/login` : 
            "https://whatsapp-platfrom-backend1.onrender.com/api/busi_users/login", {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            console.log("✅ Login successful!");
            console.log("Tokens received:", {
                access_token: data.access_token ? "✅" : "❌",
                refresh_token: data.refresh_token ? "✅" : "❌",
                busi_user: data.busi_user ? "✅" : "❌"
            });
            
            // Store tokens
            localStorage.setItem('token', data.access_token);
            localStorage.setItem('refreshToken', data.refresh_token);
            localStorage.setItem('user_role', data.busi_user.role);
            localStorage.setItem('user_id', data.busi_user.busi_user_id);
            
            console.log("✅ Tokens stored in localStorage");
            console.log("✅ You should now be able to access the dashboard");
            
        } else {
            console.log("❌ Login failed:", data.detail);
        }
        
    } catch (error) {
        console.log("❌ Simulated login error:", error.message);
    }
}

// Run all tests
console.log("Running all tests...");
testAPI().then(() => testLogin()).then(() => {
    checkForm();
    console.log("\n7. Manual login test:");
    console.log("Run simulateLogin() to try logging in with known credentials");
    console.log("Or use the login form normally and check the console");
});

// Export for manual use
window.debugLogin = {
    testAPI,
    testLogin,
    checkForm,
    simulateLogin
};

console.log("\n📋 Manual commands available:");
console.log("debugLogin.testAPI() - Test API connectivity");
console.log("debugLogin.testLogin() - Test login endpoint");
console.log("debugLogin.checkForm() - Check login form");
console.log("debugLogin.simulateLogin() - Simulate login with known credentials");
