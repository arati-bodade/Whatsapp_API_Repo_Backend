from db.session import SessionLocal
from models.busi_user import BusiUser
import json

def list_users():
    db = SessionLocal()
    try:
        users = db.query(BusiUser).limit(5).all()
        result = []
        for u in users:
            result.append({
                "id": str(u.busi_user_id),
                "email": u.email,
                "name": u.name
            })
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    list_users()
