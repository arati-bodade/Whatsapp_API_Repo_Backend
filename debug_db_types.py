from sqlalchemy import text
from db.session import SessionLocal

def check_types():
    db = SessionLocal()
    try:
        sql = """
            SELECT table_name, column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND (column_name LIKE '%id%' OR column_name LIKE '%user%')
            ORDER BY table_name, column_name
        """
        res = db.execute(text(sql))
        print(f"{'Table':<30} | {'Column':<25} | {'Type':<15}")
        print("-" * 75)
        for row in res.fetchall():
            print(f"{row[0]:<30} | {row[1]:<25} | {row[2]:<15}")
    finally:
        db.close()

if __name__ == "__main__":
    check_types()
