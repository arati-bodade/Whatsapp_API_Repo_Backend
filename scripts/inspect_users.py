import sys
import os
from sqlalchemy import create_engine, text

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from db.base import engine

def list_users():
    try:
        with engine.connect() as conn:
            # Check businesses table
            result = conn.execute(text("SELECT busi_user_id, email FROM businesses LIMIT 5"))
            print("\nExisting Users in 'businesses':")
            users = list(result)
            if not users:
                print("No users found in 'businesses'.")
            else:
                for row in users:
                    print(f"- ID: {row.busi_user_id}, Email: {row.email}")

    except Exception as e:
        print(f"Error inspecting users: {e}")

if __name__ == "__main__":
    list_users()
