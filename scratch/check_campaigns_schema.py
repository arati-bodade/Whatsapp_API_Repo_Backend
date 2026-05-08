
from db.session import get_db
from sqlalchemy import text

db = next(get_db())
try:
    result = db.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'campaigns'"))
    for row in result:
        print(f"{row[0]}: {row[1]}")
finally:
    db.close()
