from db.base import engine
from sqlalchemy import text
with engine.connect() as conn:
    res = conn.execute(text('SELECT * FROM plans'))
    rows = res.fetchall()
    print(f"PLANS_FETCHED:{len(rows)}")
    for r in rows:
        print(r)
