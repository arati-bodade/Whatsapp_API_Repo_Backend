from sqlalchemy import text
from db.session import engine

def get_reseller_password():
    email = "lungeom39@gmail.com"
    print(f"Searching for reseller with email: {email}...")
    
    with engine.connect() as connection:
        try:
            # Query for reseller by email
            res = connection.execute(text("SELECT * FROM resellers WHERE email = :email;"), {"email": email}).fetchone()
            
            if res:
                # Convert Row to dict
                columns = res._fields
                data = dict(zip(columns, res))
                
                print(f"\n=== RESELLER FOUND ===")
                print(f"Name: {data.get('name', 'N/A')}")
                print(f"Username: {data.get('username', 'N/A')}")
                print(f"Email: {data.get('email', 'N/A')}")
                print(f"Phone: {data.get('phone', 'N/A')}")
                print(f"Status: {data.get('status', 'N/A')}")
                print(f"Role: {data.get('role', 'N/A')}")
                print(f"Business Name: {data.get('business_name', 'N/A')}")
                print(f"Created At: {data.get('created_at', 'N/A')}")
                print(f"\n=== PASSWORD INFORMATION ===")
                print(f"Password Hash: {data.get('password_hash', 'N/A')}")
                
                # Note: The password is stored as a hash, not plain text
                print(f"\nNOTE: Password is stored as hash for security.")
                print(f"The actual password cannot be retrieved, only the hash.")
                
            else:
                print(f"\n=== NO RESELLER FOUND ===")
                print(f"No reseller found with email: {email}")
                
                # Let's check if there are any resellers with similar email
                similar_resellers = connection.execute(
                    text("SELECT email, name, username FROM resellers WHERE email LIKE '%gmail.com%' LIMIT 5;")
                ).fetchall()
                
                if similar_resellers:
                    print(f"\n=== SIMILAR RESELLERS (gmail.com) ===")
                    for reseller in similar_resellers:
                        print(f"Email: {reseller[0]}, Name: {reseller[1]}, Username: {reseller[2]}")
                
        except Exception as e:
            print(f"Error querying database: {e}")

if __name__ == "__main__":
    get_reseller_password()
