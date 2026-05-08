import bcrypt
from sqlalchemy import text
from db.session import engine

def update_reseller_password():
    email = "lungeom39@gmail.com"
    new_password = "lunge@123"
    
    print(f"Updating password for reseller: {email}")
    print(f"New password: {new_password}")
    
    # Hash the new password using bcrypt
    password_bytes = new_password.encode('utf-8')
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password_bytes, salt)
    
    # Convert to string for storage
    password_hash_str = password_hash.decode('utf-8')
    
    print(f"Generated password hash: {password_hash_str}")
    
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
                {"password_hash": password_hash_str, "email": email}
            )
            
            # Commit the transaction
            connection.commit()
            
            if result.rowcount > 0:
                print(f"\n=== PASSWORD UPDATE SUCCESSFUL ===")
                print(f"Updated {result.rowcount} record(s)")
                print(f"Password for {email} has been updated successfully")
                
                # Verify the update by fetching the record
                verify_query = text("SELECT username, email, updated_at FROM resellers WHERE email = :email")
                verify_result = connection.execute(verify_query, {"email": email}).fetchone()
                
                if verify_result:
                    print(f"\n=== VERIFICATION ===")
                    print(f"Username: {verify_result[0]}")
                    print(f"Email: {verify_result[1]}")
                    print(f"Updated At: {verify_result[2]}")
                
            else:
                print(f"\n=== UPDATE FAILED ===")
                print(f"No records found for email: {email}")
                
        except Exception as e:
            print(f"Error updating password: {e}")
            connection.rollback()

if __name__ == "__main__":
    update_reseller_password()
