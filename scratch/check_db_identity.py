
from db.session import get_db
from sqlalchemy import text

db = next(get_db())
try:
    result = db.execute(text("SELECT current_database(), current_schema(), inet_server_addr()"))
    for row in result:
        print(f"Database: {row[0]}")
        print(f"Schema: {row[1]}")
        print(f"Server Addr: {row[2]}")
        
    result = db.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'master_admins' AND column_name = 'admin_id'"))
    for row in result:
        print(f"Column: {row[0]}, Type: {row[1]}")
finally:
    db.close()
