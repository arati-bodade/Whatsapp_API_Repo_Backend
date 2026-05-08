from db.base import engine, Base
from models.device import Device
from sqlalchemy import text

def reset_db_enums():
    print("Starting DB Enum Reset...")
    with engine.connect() as conn:
        conn.execution_options(isolation_level="AUTOCOMMIT")
        
        # 1. Drop table
        print("Dropping devices table...")
        try:
            conn.execute(text("DROP TABLE IF EXISTS devices CASCADE"))
            print("Table dropped.")
        except Exception as e:
            print(f"Error dropping table: {e}")

        # 2. Drop enums
        print("Dropping enum types...")
        try:
            conn.execute(text("DROP TYPE IF EXISTS devicetype CASCADE"))
            conn.execute(text("DROP TYPE IF EXISTS sessionstatus CASCADE"))
            print("Enums dropped.")
        except Exception as e:
            print(f"Error dropping enums: {e}")
            
    # 3. Recreate all
    print("Recreating schema...")
    Base.metadata.create_all(bind=engine)
    print("Schema recreated successfully.")

if __name__ == "__main__":
    reset_db_enums()
