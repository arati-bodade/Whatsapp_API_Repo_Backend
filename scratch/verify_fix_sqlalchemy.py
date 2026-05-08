
from db.session import get_db
from models.admin import MasterAdmin
import uuid

db = next(get_db())
try:
    print("Testing MasterAdmin query with UUID object...")
    # This was the failing query in the user's log
    user_id = "db7bc700-2c51-4aa8-820d-bf9150f9339a" # From user's log
    user_uuid = uuid.UUID(user_id)
    
    admin = db.query(MasterAdmin).filter(MasterAdmin.admin_id == user_uuid).first()
    if admin:
        print(f"✅ Success! Admin found: {admin.username}")
    else:
        # Try finding ANY admin to confirm query works
        admin = db.query(MasterAdmin).first()
        if admin:
            print(f"✅ Success! Found another admin: {admin.username} with ID {admin.admin_id}")
        else:
            print("⚠️ No admins found, but query succeeded.")
finally:
    db.close()
