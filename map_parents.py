from db.session import SessionLocal
from models.reseller import Reseller
from models.busi_user import BusiUser

def map_parents():
    db = SessionLocal()
    resellers = db.query(Reseller).all()
    r_map = {r.reseller_id: r.name for r in resellers}
    
    users = db.query(BusiUser).all()
    print(f"{'User Name':30} | {'Email':30} | {'Parent Reseller':30}")
    print("-" * 95)
    for u in users:
        p_name = r_map.get(u.parent_reseller_id, "Unknown (ID: " + str(u.parent_reseller_id) + ")")
        print(f"{u.name:30} | {u.email:30} | {p_name:30}")

if __name__ == "__main__":
    map_parents()
