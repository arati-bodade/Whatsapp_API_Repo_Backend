from db.base import engine, Base
from models import * # This now includes WhatsAppInbox via __init__

def create_tables():
    print("Creating all tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("Tables created successfully.")
    except Exception as e:
        print(f"Error creating tables: {e}")

if __name__ == "__main__":
    create_tables()
