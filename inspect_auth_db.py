from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models.busi_user import BusiUser
from models.reseller import Reseller
from db.base import Base, get_db
import os
from dotenv import load_dotenv

load_dotenv()

# Setup pure SQLAlchemy connection to avoid app overhead
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def inspect_hashes():
    db = SessionLocal()
    try:
        print("\n--- Inspecting Resellers (First 20) ---")
        resellers = db.query(Reseller).limit(20).all()
        for r in resellers:
            is_bcrypt = r.password_hash.startswith("$2b$") or r.password_hash.startswith("$2a$")
            status = "BCRYPT" if is_bcrypt else "POSSIBLE PLAIN/OTHER"
            print(f"Reseller: {r.email:30} | HashPrefix: {r.password_hash[:10]:10} | Len: {len(r.password_hash)} | Type: {status}")

        print("\n--- Inspecting BusiUsers (First 20) ---")
        users = db.query(BusiUser).limit(20).all()
        for u in users:
            is_bcrypt = u.password_hash.startswith("$2b$") or u.password_hash.startswith("$2a$")
            status = "BCRYPT" if is_bcrypt else "POSSIBLE PLAIN/OTHER"
            print(f"User: {u.email:30} | HashPrefix: {u.password_hash[:10]:10} | Len: {len(u.password_hash)} | Type: {status}")
            
    finally:
        db.close()

if __name__ == "__main__":
    inspect_hashes()
