from db.base import engine
from sqlalchemy import text
with engine.connect() as conn:
    res = conn.execute(text('SELECT admin_id, username, profile_image FROM master_admins'))
    rows = res.fetchall()
    for r in rows:
        print(r)
