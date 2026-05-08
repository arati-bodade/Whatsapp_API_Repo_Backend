from sqlalchemy import inspect
from db.base import engine

def list_tables():
    inspector = inspect(engine)
    for table_name in inspector.get_table_names():
        print(f"Table: {table_name}")
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        print(f"  Columns: {', '.join(columns)}")
        print("-" * 20)

if __name__ == "__main__":
    list_tables()
