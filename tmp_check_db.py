from db.session import SessionLocal
from models.busi_user import BusiUser
from models.reseller import Reseller
from models.admin import MasterAdmin

db = SessionLocal()
try:
    print("--- BusiUsers (First 3) ---")
    users = db.query(BusiUser).limit(3).all()
    for u in users:
        cb = getattr(u, "created_by", "COL_MISSING")
        print(f"Name: {u.name} | ParRes: {u.parent_reseller_id} | ParRole: {u.parent_role} | CB: {cb}")
    
    print("\n--- Resellers (First 3) ---")
    resellers = db.query(Reseller).limit(3).all()
    for r in resellers:
        cb = getattr(r, "created_by", "COL_MISSING")
        print(f"Name: {r.name} | CB: {cb}")
finally:
    db.close()
