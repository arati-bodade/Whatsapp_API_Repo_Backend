from db.session import SessionLocal
from sqlalchemy import text
from core.security import get_password_hash
import uuid

def create_reseller_raw():
    db = SessionLocal()
    email = "rohit.mehta@example.com"
    password = "Rohit@Pass999"
    hashed = get_password_hash(password)
    reseller_id = str(uuid.uuid4())
    
    # Check existence
    check_sql = text("SELECT reseller_id FROM resellers WHERE email = :email")
    result = db.execute(check_sql, {"email": email}).fetchone()
    
    if result:
        print(f"Reseller exists: {result[0]}. Updating password...")
        update_sql = text("UPDATE resellers SET password_hash = :pwd WHERE email = :email")
        db.execute(update_sql, {"pwd": hashed, "email": email})
        db.commit()
    else:
        print(f"Creating reseller {email} with ID {reseller_id}...")
        insert_sql = text("""
            INSERT INTO resellers (reseller_id, email, username, name, phone, password_hash, role, status, created_at, updated_at)
            VALUES (:rid, :email, :username, :name, :phone, :pwd, 'reseller', 'active', NOW(), NOW())
        """)
        db.execute(insert_sql, {
            "rid": reseller_id,
            "email": email,
            "username": "rohit_reseller",
            "name": "Rohit Mehta",
            "phone": "9999999999",
            "pwd": hashed
        })
        db.commit()
        print("Reseller created successfully via Raw SQL.")
    
    db.close()

if __name__ == "__main__":
    create_reseller_raw()
