from sqlalchemy import text
from db.session import engine

def check_duplicate_resellers():
    email = "lungeom39@gmail.com"
    
    print(f"=== CHECKING FOR DUPLICATE RESELLERS ===")
    print(f"Email: {email}")
    
    with engine.connect() as connection:
        try:
            # Check for exact matches
            exact_query = text("""
                SELECT reseller_id, email, username, name, status, created_at 
                FROM resellers 
                WHERE email = :email
                ORDER BY created_at
            """)
            
            exact_results = connection.execute(exact_query, {"email": email}).fetchall()
            
            print(f"\n=== EXACT EMAIL MATCHES ===")
            if exact_results:
                for i, res in enumerate(exact_results, 1):
                    print(f"{i}. ID: {res[0]}, Email: {res[1]}, Username: {res[2]}, Name: {res[3]}, Status: {res[4]}, Created: {res[5]}")
            else:
                print("No exact matches found")
            
            # Check for similar emails (case insensitive)
            similar_query = text("""
                SELECT reseller_id, email, username, name, status, created_at 
                FROM resellers 
                WHERE LOWER(email) = LOWER(:email)
                ORDER BY created_at
            """)
            
            similar_results = connection.execute(similar_query, {"email": email}).fetchall()
            
            print(f"\n=== CASE-INSENSITIVE MATCHES ===")
            if similar_results:
                for i, res in enumerate(similar_results, 1):
                    print(f"{i}. ID: {res[0]}, Email: {res[1]}, Username: {res[2]}, Name: {res[3]}, Status: {res[4]}, Created: {res[5]}")
            else:
                print("No case-insensitive matches found")
            
            # Check for emails with extra spaces
            space_query = text("""
                SELECT reseller_id, email, username, name, status, created_at 
                FROM resellers 
                WHERE TRIM(email) = TRIM(:email)
                ORDER BY created_at
            """)
            
            space_results = connection.execute(space_query, {"email": email}).fetchall()
            
            print(f"\n=== TRIMMED EMAIL MATCHES ===")
            if space_results:
                for i, res in enumerate(space_results, 1):
                    print(f"{i}. ID: {res[0]}, Email: '{res[1]}', Username: {res[2]}, Name: {res[3]}, Status: {res[4]}, Created: {res[5]}")
                    # Show if there are leading/trailing spaces
                    if res[1] != res[1].strip():
                        print(f"   ⚠️  Email has spaces: '{res[1]}' -> '{res[1].strip()}'")
            else:
                print("No trimmed email matches found")
            
            # Check all resellers with gmail.com to see if there are similar accounts
            gmail_query = text("""
                SELECT reseller_id, email, username, name, status, created_at 
                FROM resellers 
                WHERE email LIKE '%gmail.com%'
                ORDER BY created_at
                LIMIT 10
            """)
            
            gmail_results = connection.execute(gmail_query).fetchall()
            
            print(f"\n=== ALL GMAIL.COM RESELLERS (LIMIT 10) ===")
            if gmail_results:
                for i, res in enumerate(gmail_results, 1):
                    print(f"{i}. ID: {res[0]}, Email: {res[1]}, Username: {res[2]}, Name: {res[3]}, Status: {res[4]}")
            else:
                print("No gmail.com accounts found")
                
        except Exception as e:
            print(f"Error checking duplicates: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    check_duplicate_resellers()
