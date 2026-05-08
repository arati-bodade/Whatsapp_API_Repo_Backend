import sys
sys.path.append('.')
from db.session import SessionLocal
from models.busi_user import BusiUser

db = SessionLocal()

print('=== Debug Credit Balance Issue ===')

# Check Om Lunge's account directly
om_lunge = db.query(BusiUser).filter(BusiUser.email == 'lungeom39@gmail.com').first()
if om_lunge:
    print(f'✅ Found Om Lunge Account:')
    print(f'  Business Name: {om_lunge.business_name}')
    print(f'  User ID: {om_lunge.busi_user_id}')
    print(f'  Email: {om_lunge.email}')
    print(f'  Credits Remaining: {om_lunge.credits_remaining}')
    print(f'  Credits Allocated: {om_lunge.credits_allocated}')
    print(f'  Credits Used: {om_lunge.credits_used}')
    
    # Check if the balance API response format is correct
    api_response = {
        "user_id": str(om_lunge.busi_user_id),
        "user_type": "business",
        "current_balance": max(0, om_lunge.credits_remaining or 0),
        "credits_used": max(0, om_lunge.credits_used or 0)
    }
    
    print(f'\\n✅ API Response Format:')
    print(f'  {api_response}')
    
    print(f'\\n✅ Frontend Should Display:')
    print(f'  Current Balance: {api_response["current_balance"]}')
    print(f'  Credits Used: {api_response["credits_used"]}')
    
else:
    print('❌ Om Lunge account not found')

db.close()

print(f'\\n🔧 If frontend shows "---" instead of credits:')
print(f'  1. Check browser console for API errors')
print(f'  2. Verify authentication token is valid')
print(f'  3. Check network connectivity to backend')
print(f'  4. Verify API endpoint is accessible')
