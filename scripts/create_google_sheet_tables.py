
import sys
import os

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.base import engine, Base
# Import all models to ensure they are registered with Base
from models import * 
from models.google_sheet import GoogleSheet, SheetTriggerHistory

def create_tables():
    print("Creating Google Sheet tables...")
    # This will only create tables that don't exist
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")

if __name__ == "__main__":
    create_tables()
