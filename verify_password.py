import bcrypt
from sqlalchemy import text
from db.session import engine

def verify_password():
    email = "lungeom39@gmail.com"
    test_password = "lunge@123"
    
    print(f"Verifying password for: {email}")
    print(f"Test password: {test_password}")
    
    with engine.connect() as connection:
        try:
            # Get the current password hash
            res = connection.execute(text("SELECT password_hash FROM resellers WHERE email = :email;"), {"email": email}).fetchone()
            
            if res:
                stored_hash = res[0]
                print(f"Stored hash: {stored_hash}")
                
                # Test the password against the stored hash
                password_bytes = test_password.encode('utf-8')
                hash_bytes = stored_hash.encode('utf-8')
                
                # Check if password matches
                is_valid = bcrypt.checkpw(password_bytes, hash_bytes)
                
                print(f"\n=== PASSWORD VERIFICATION ===")
                print(f"Password matches: {is_valid}")
                
                if is_valid:
                    print("✅ Password verification successful!")
                else:
                    print("❌ Password verification failed!")
                    
                    # Let's also test with some common variations
                    test_variations = [
                        "lunge@123",
                        "Lunge@123", 
                        "lunge@123 ",
                        " lunge@123"
                    ]
                    
                    print(f"\n=== TESTING VARIATIONS ===")
                    for variation in test_variations:
                        test_bytes = variation.encode('utf-8')
                        variation_valid = bcrypt.checkpw(test_bytes, hash_bytes)
                        print(f"'{variation}': {'✅' if variation_valid else '❌'}")
                
            else:
                print(f"No reseller found with email: {email}")
                
        except Exception as e:
            print(f"Error verifying password: {e}")

if __name__ == "__main__":
    verify_password()
