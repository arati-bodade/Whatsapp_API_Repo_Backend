
from db.session import get_db
from sqlalchemy import text

db = next(get_db())
try:
    result = db.execute(text("""
        SELECT column_name, data_type, udt_name 
        FROM information_schema.columns 
        WHERE table_name = 'master_admins' AND column_name = 'admin_id';
    """))
    for row in result:
        print(f"Column: {row[0]}")
        print(f"Data Type: {row[1]}")
        print(f"UDT Name: {row[2]}")
finally:
    db.close()
