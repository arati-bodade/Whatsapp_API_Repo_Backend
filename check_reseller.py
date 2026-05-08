from sqlalchemy import text
from db.session import engine

def check_reseller_data():
    name = "Akshay Patil"
    print(f"Checking data for reseller: {name}...")
    with engine.connect() as connection:
        try:
            res = connection.execute(text("SELECT * FROM resellers WHERE name = :name;"), {"name": name}).fetchone()
            if res:
                # Convert Row to dict
                columns = res._fields
                data = dict(zip(columns, res))
                print("\nReseller found:")
                for k, v in data.items():
                    if k != 'password_hash':
                        print(f"  {k}: {v}")
            else:
                print(f"\nReseller not found with name: {name}")
                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    check_reseller_data()
