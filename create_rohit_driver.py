import psycopg2
import uuid
import os
from passlib.hash import bcrypt

# Database connection details
DB_URL = "postgresql://whatsapp_patform_user:cCR4XEVKwlV3XdoOmWbGw6rdNTyBOppm@dpg-d5fp9qlactks739q3o20-a.oregon-postgres.render.com/whatsapp_patform?sslmode=require"

def create_reseller_driver():
    print("Connecting to database...")
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        print("Connected.")
        
        email = "rohit.mehta@example.com"
        password = "Rohit@Pass999"
        
        # Hash password using passlib directly (avoiding core.security imports)
        password_hash = bcrypt.hash(password)
        reseller_id = str(uuid.uuid4())
        
        # Check existence
        print(f"Checking if {email} exists...")
        cur.execute("SELECT reseller_id FROM resellers WHERE email = %s", (email,))
        existing = cur.fetchone()
        
        if existing:
            print(f"Reseller exists with ID {existing[0]}. Updating password...")
            cur.execute("UPDATE resellers SET password_hash = %s WHERE email = %s", (password_hash, email))
            conn.commit()
            print("Password updated.")
        else:
            print(f"Creating reseller {email}...")
            cur.execute("""
                INSERT INTO resellers (
                    reseller_id, email, username, name, phone, password_hash, role, status, created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, 'reseller', 'active', NOW(), NOW()
                )
            """, (reseller_id, email, "rohit_reseller", "Rohit Mehta", "9999999900", password_hash))
            
            # Also create analytics row to prevent frontend 500
            print("Creating analytics...")
            cur.execute("""
                INSERT INTO reseller_analytics (
                    reseller_id, total_credits_purchased, total_credits_distributed, 
                    total_credits_used, remaining_credits, business_user_stats, 
                    generated_at, updated_at
                ) VALUES (
                    %s, 1000, 0, 0, 1000, '[]'::json, NOW(), NOW()
                )
            """, (reseller_id,))
            
            conn.commit()
            print("Reseller and Analytics created successfully.")
            
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    create_reseller_driver()
