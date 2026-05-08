import psycopg2
import os

# Database connection details
DB_URL = "postgresql://whatsapp_patform_user:cCR4XEVKwlV3XdoOmWbGw6rdNTyBOppm@dpg-d5fp9qlactks739q3o20-a.oregon-postgres.render.com/whatsapp_patform?sslmode=require"

def fix_wallet():
    print("Connecting to database...")
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        print("Connected.")
        
        email = "rohit.mehta@example.com"
        
        print(f"Fixing wallet for {email}...")
        cur.execute("""
            UPDATE resellers 
            SET total_credits = 0, available_credits = 0, used_credits = 0 
            WHERE email = %s
        """, (email,))
        
        conn.commit()
        print("Wallet fields updated successfully.")
            
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    fix_wallet()
