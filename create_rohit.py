from db.session import SessionLocal
from models.reseller import Reseller
from core.security import get_password_hash
import uuid

def create_reseller():
    db = SessionLocal()
    email = "rohit.mehta@example.com"
    password = "Rohit@Pass999"
    
    # Check if exists
    existing = db.query(Reseller).filter(Reseller.email == email).first()
    if existing:
        print(f"Reseller {email} already exists. Updating password...")
        existing.password_hash = get_password_hash(password)
        db.commit()
        print("Password updated.")
    else:
        print(f"Creating reseller {email}...")
        new_reseller = Reseller(
            reseller_id=uuid.uuid4(),
            email=email,
            username="rohit_reseller",
            name="Rohit Mehta",
            phone="9999999999",
            password_hash=get_password_hash(password),
            role="reseller",
            status="active"
        )
        db.add(new_reseller)
        db.commit()
        print("Reseller created successfully.")
    db.close()

if __name__ == "__main__":
    create_reseller()
