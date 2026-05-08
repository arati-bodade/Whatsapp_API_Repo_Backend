from core.security import get_password_hash, verify_password
from sqlalchemy import text
from db.session import engine

def fix_reseller_password():
    email = "lungeom39@gmail.com"
    new_password = "lunge@123"
    
    print(f"Fixing password for reseller: {email}")
    print(f"New password: {new_password}")
    
    # Hash the password using the same method as the system
    password_hash = get_password_hash(new_password)
    
    print(f"Generated password hash: {password_hash}")
    
    with engine.connect() as connection:
        try:
            # Update the password in the database
            update_query = text("""
                UPDATE resellers 
                SET password_hash = :password_hash, updated_at = CURRENT_TIMESTAMP 
                WHERE email = :email
            """)
            
            result = connection.execute(
                update_query, 
                {"password_hash": password_hash, "email": email}
            )
            
            # Commit the transaction
            connection.commit()
            
            if result.rowcount > 0:
                print(f"\n=== PASSWORD UPDATE SUCCESSFUL ===")
                print(f"Updated {result.rowcount} record(s)")
                
                # Verify the password works
                print(f"\n=== VERIFYING PASSWORD ===")
                stored_hash = password_hash
                is_valid = verify_password(new_password, stored_hash)
                print(f"Password verification: {'✅ SUCCESS' if is_valid else '❌ FAILED'}")
                
                # Get updated record info
                verify_query = text("SELECT username, email, updated_at FROM resellers WHERE email = :email")
                verify_result = connection.execute(verify_query, {"email": email}).fetchone()
                
                if verify_result:
                    print(f"\n=== UPDATED RECORD ===")
                    print(f"Username: {verify_result[0]}")
                    print(f"Email: {verify_result[1]}")
                    print(f"Updated At: {verify_result[2]}")
                
                print(f"\n=== LOGIN TEST ===")
                print(f"Try logging in with:")
                print(f"Email: {email}")
                print(f"Password: {new_password}")
                
            else:
                print(f"\n=== UPDATE FAILED ===")
                print(f"No records found for email: {email}")
                
        except Exception as e:
            print(f"Error updating password: {e}")
            connection.rollback()

if __name__ == "__main__":
    fix_reseller_password()
