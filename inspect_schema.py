from sqlalchemy import create_engine, inspect
from core.config import settings

def inspect_db():
    engine = create_engine(settings.DATABASE_URL)
    inspector = inspect(engine)
    
    with open("schema_info.txt", "w") as f:
        f.write("Columns in 'resellers' table:\n")
        columns = inspector.get_columns('resellers')
        for column in columns:
            f.write(f"- {column['name']} ({column['type']})\n")
            if column.get('primary_key'):
                f.write(f"  * PRIMARY KEY\n")

if __name__ == "__main__":
    inspect_db()
