import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db.session import SessionLocal
from models.reseller import Reseller
from models.busi_user import BusiUser

def main():
    db = SessionLocal()
    try:
        resellers = db.query(Reseller).all()
        businesses = db.query(BusiUser).all()
        
        with open("out.txt", "w", encoding="utf-8") as f:
            f.write("------- RESELLERS -------\n")
            for r in resellers:
                d = dict(r.__dict__)
                d.pop('_sa_instance_state', None)
                display_dict = {k: str(v) for k, v in d.items() if k in ['reseller_id', 'name', 'email', 'phone', 'status', 'total_credits']}
                f.write(str(display_dict) + "\n")
                
            f.write("\n------- BUSINESS USERS -------\n")
            for b in businesses:
                d = dict(b.__dict__)
                d.pop('_sa_instance_state', None)
                display_dict = {k: str(v) for k, v in d.items() if k in ['busi_user_id', 'business_name', 'name', 'email', 'phone', 'status', 'parent_reseller_id', 'plan_id']}
                f.write(str(display_dict) + "\n")
            
    finally:
        db.close()

if __name__ == "__main__":
    main()
