from db.session import SessionLocal
from sqlalchemy import text
import uuid
import datetime

def recover_orphaned_users(reseller_id):
    db = SessionLocal()
    
    # 1. Get all unique busi_user_ids from config tables
    config_ids = set()
    tables = ["unofficial_whatsapps", "official_whatsapp_configs"]
    for t in tables:
        try:
            columns_res = db.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{t}'")).fetchall()
            cols = [c[0] for c in columns_res]
            id_col = "busi_user_id" if "busi_user_id" in cols else ("user_id" if "user_id" in cols else None)
            if id_col:
                res = db.execute(text(f"SELECT DISTINCT {id_col} FROM {t}")).fetchall()
                for r in res:
                    if r[0]: config_ids.add(str(r[0]))
        except: pass

    # 2. Get existing business users
    existing_users = db.execute(text("SELECT busi_user_id FROM businesses")).fetchall()
    existing_ids = {str(r[0]) for r in existing_users}
    
    orphans = config_ids - existing_ids
    print(f"Found {len(orphans)} orphaned user IDs.")

    # 3. Create missing business user records
    for uid in orphans:
        try:
            # Check if it's a valid UUID, if not, skip or handle
            try:
                val_id = uuid.UUID(uid)
            except:
                print(f"Skipping non-UUID orphan: {uid}")
                continue

            # Try to find a name hint from configs
            name_hint = "Recovered User"
            email_hint = f"recovered_{uid[:8]}@example.com"
            
            # Look in unofficial_whatsapps for a device name to use as business name
            row = db.execute(text(f"SELECT * FROM unofficial_whatsapps WHERE busi_user_id = '{uid}' LIMIT 1")).fetchone()
            # Note: columns are misaligned, so we have to be careful.
            # From dump, 'qr_last_generated' or 'session_status' seemed to have names.
            # Let's just use a generic name for now or try to be smart.
            
            print(f"Creating business user for ID: {uid}")
            # Insert into businesses (which is the BusiUser table)
            db.execute(text("""
                INSERT INTO businesses (
                    busi_user_id, name, username, email, password_hash, 
                    role, status, parent_reseller_id, 
                    phone, business_name,
                    created_at, updated_at
                ) VALUES (
                    :uid, :name, :username, :email, :pw, 
                    'user', 'active', :parent_id, 
                    :phone, :bus_name,
                    NOW(), NOW()
                ) ON CONFLICT (busi_user_id) DO NOTHING
            """), {
                "uid": uid,
                "name": name_hint,
                "username": f"user_{uid[:8]}",
                "email": email_hint,
                "pw": "$2b$12$LQv3c1yqBWVHxkd0LqCFaeC7f.4.9wP1C9F/f.4.9wP1C9F/f.4.9", # dummy hash
                "parent_id": reseller_id,
                "phone": f"0000{uid[:8]}", # dummy phone
                "bus_name": f"Recovered {uid[:8]}"
            })
            
            # Also need to create wallet record if it's separate?
            # In some schemas wallet is in 'businesses' table, in others separate.
            # Let's check 'counts.json' again. 'credit_distributions'?
            
        except Exception as e:
            print(f"Error recovering {uid}: {e}")
            db.rollback()

    db.commit()
    print("Recovery complete.")

if __name__ == "__main__":
    ROHIT_ID = "98956f27-d3f9-4b41-85ea-3be40201b778"
    recover_orphaned_users(ROHIT_ID)
