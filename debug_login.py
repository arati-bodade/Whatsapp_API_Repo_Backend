from core.security import verify_password, get_password_hash
from sqlalchemy import text
from db.session import engine
from services.reseller_service import ResellerService

def debug_login_process():
    email = "lungeom39@gmail.com"
    password = "lunge@123"
    
    print(f"=== DEBUGGING LOGIN PROCESS ===")
    print(f"Email: {email}")
    print(f"Password: {password}")
    
    # Step 1: Check database connection and get reseller data
    print(f"\n=== STEP 1: DATABASE QUERY ===")
    with engine.connect() as connection:
        try:
            res = connection.execute(text("SELECT * FROM resellers WHERE email = :email;"), {"email": email}).fetchone()
            
            if res:
                columns = res._fields
                data = dict(zip(columns, res))
                
                print(f"✅ Reseller found in database")
                print(f"Name: {data.get('name')}")
                print(f"Username: {data.get('username')}")
                print(f"Status: {data.get('status')}")
                print(f"Password Hash: {data.get('password_hash')}")
                
                stored_hash = data.get('password_hash')
                
            else:
                print(f"❌ Reseller not found in database")
                return
                
        except Exception as e:
            print(f"❌ Database error: {e}")
            return
    
    # Step 2: Test password verification directly
    print(f"\n=== STEP 2: PASSWORD VERIFICATION ===")
    try:
        is_valid = verify_password(password, stored_hash)
        print(f"Password verification result: {'✅ SUCCESS' if is_valid else '❌ FAILED'}")
        
        if not is_valid:
            print(f"Testing password against hash:")
            print(f"Input password: '{password}'")
            print(f"Stored hash: {stored_hash}")
            
            # Test with fresh hash
            fresh_hash = get_password_hash(password)
            print(f"Fresh hash: {fresh_hash}")
            fresh_valid = verify_password(password, fresh_hash)
            print(f"Fresh hash verification: {'✅ SUCCESS' if fresh_valid else '❌ FAILED'}")
            
    except Exception as e:
        print(f"❌ Password verification error: {e}")
        return
    
    # Step 3: Test ResellerService.get_reseller_by_email
    print(f"\n=== STEP 3: RESELLER SERVICE TEST ===")
    try:
        from db.session import SessionLocal
        db = SessionLocal()
        try:
            reseller_service = ResellerService(db)
            reseller = reseller_service.get_reseller_by_email(email.lower().strip())
            
            if reseller:
                print(f"✅ ResellerService found reseller")
                print(f"Service returned email: {reseller.email}")
                print(f"Service returned status: {reseller.status}")
                print(f"Service returned hash: {reseller.password_hash}")
                
                # Test verification with service data
                service_valid = verify_password(password, reseller.password_hash)
                print(f"Service data verification: {'✅ SUCCESS' if service_valid else '❌ FAILED'}")
                
            else:
                print(f"❌ ResellerService returned None")
                
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ ResellerService error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 4: Simulate full login logic
    print(f"\n=== STEP 4: FULL LOGIN SIMULATION ===")
    try:
        from db.session import SessionLocal
        db = SessionLocal()
        try:
            # Normalize email (same as login endpoint)
            normalized_email = email.lower().strip()
            print(f"Normalized email: '{normalized_email}'")
            
            reseller_service = ResellerService(db)
            reseller = reseller_service.get_reseller_by_email(normalized_email)
            
            if not reseller:
                print(f"❌ No reseller found with normalized email")
                return
            
            if reseller.status != "active":
                print(f"❌ Reseller status is not active: {reseller.status}")
                return
            
            # Password verification (same as login endpoint)
            password_valid = False
            
            if verify_password(password, reseller.password_hash):
                password_valid = True
                print(f"✅ Primary password verification passed")
            elif reseller.password_hash == password.strip():
                password_valid = True
                print(f"✅ Plain text password fallback passed")
            else:
                print(f"❌ Both password verification methods failed")
            
            if password_valid:
                print(f"✅ Full login simulation SUCCESS")
                print(f"Reseller can login with:")
                print(f"Email: {email}")
                print(f"Password: {password}")
            else:
                print(f"❌ Full login simulation FAILED")
                
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Login simulation error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_login_process()
