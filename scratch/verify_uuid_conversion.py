
from db.session import get_db
from sqlalchemy import text

db = next(get_db())
try:
    for table, col in [('master_admins', 'admin_id'), ('resellers', 'reseller_id'), ('businesses', 'busi_user_id')]:
        result = db.execute(text(f"""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = '{table}' AND column_name = '{col}';
        """))
        for row in result:
            print(f"{table}.{col}: {row[1]}")
finally:
    db.close()
