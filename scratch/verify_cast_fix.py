
from db.session import get_db
from models.admin import MasterAdmin
from sqlalchemy import cast
from sqlalchemy.dialects.postgresql import UUID as SQL_UUID
import uuid

db = next(get_db())
try:
    print("Testing MasterAdmin query with explicit CAST...")
    user_id = "db7bc700-2c51-4aa8-820d-bf9150f9339a"
    user_uuid = uuid.UUID(user_id)
    
    # Use the same logic as now in api/auth.py
    admin = db.query(MasterAdmin).filter(cast(MasterAdmin.admin_id, SQL_UUID) == user_uuid).first()
    if admin:
        print(f"✅ Success! Admin found: {admin.username}")
    else:
        # Try finding ANY admin to confirm query works
        admin = db.query(MasterAdmin).filter(cast(MasterAdmin.admin_id, SQL_UUID).isnot(None)).first()
        if admin:
            print(f"✅ Success! Found another admin: {admin.username} with ID {admin.admin_id}")
        else:
            print("⚠️ No admins found, but query succeeded.")
finally:
    db.close()
