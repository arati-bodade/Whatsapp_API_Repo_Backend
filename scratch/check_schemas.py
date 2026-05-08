
from db.session import get_db
from sqlalchemy import text

db = next(get_db())
try:
    result = db.execute(text("SELECT table_schema, table_name FROM information_schema.tables WHERE table_name = 'master_admins'"))
    for row in result:
        print(f"Table: {row[0]}.{row[1]}")
    
    # Also check the search path
    result = db.execute(text("SHOW search_path"))
    for row in result:
        print(f"Search Path: {row[0]}")
finally:
    db.close()
