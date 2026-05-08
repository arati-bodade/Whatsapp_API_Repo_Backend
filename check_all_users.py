from db.session import SessionLocal
from models.admin import MasterAdmin
from models.reseller import Reseller
from models.busi_user import BusiUser
import uuid

def check_all_user_types(target_user_id):
    db = SessionLocal()
    try:
        user_uuid = uuid.UUID(target_user_id)
        
        admin = db.query(MasterAdmin).filter(MasterAdmin.admin_id == user_uuid).first()
        if admin:
            print(f"✅ Found in MasterAdmin: {admin.name} ({admin.email})")
            return

        reseller = db.query(Reseller).filter(Reseller.reseller_id == user_uuid).first()
        if reseller:
            print(f"✅ Found in Reseller: {reseller.name} ({reseller.email})")
            return

        busi = db.query(BusiUser).filter(BusiUser.busi_user_id == user_uuid).first()
        if busi:
            print(f"✅ Found in BusiUser: {busi.name} ({busi.email})")
            return
            
        print(f"❌ ID {target_user_id} not found in any user table")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_all_user_types("a6b02694-8e95-4c4e-9fce-841e7eb1b3f0")
