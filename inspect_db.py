from sqlalchemy import text
from db.session import SessionLocal, engine

def inspect():
    with engine.connect() as connection:
        res = connection.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'plans'
        """)).fetchall()
        for row in res:
            print(row)

if __name__ == "__main__":
    inspect()
