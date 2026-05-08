from db.session import SessionLocal
from models.reseller import Reseller
from models.busi_user import BusiUser
import json

def dump_data():
    db = SessionLocal()
    resellers = db.query(Reseller).all()
    r_list = []
    for r in resellers:
        r_list.append({
            "id": str(r.reseller_id),
            "name": r.name,
            "email": r.email
        })
    
    users = db.query(BusiUser).all()
    u_list = []
    for u in users:
        u_list.append({
            "id": str(u.busi_user_id),
            "name": u.name,
            "email": u.email,
            "parent_id": str(u.parent_reseller_id) if u.parent_reseller_id else None
        })
    
    with open("db_dump.json", "w") as f:
        json.dump({"resellers": r_list, "users": u_list}, f, indent=4)
    print("Dump complete")

if __name__ == "__main__":
    dump_data()
