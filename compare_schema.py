import os
import sys
from sqlalchemy import create_engine, inspect
from dotenv import load_dotenv

# Add project root to sys.path
sys.path.append(os.getcwd())

load_dotenv()

# Import models
from models.busi_user import BusiUser
from models.device import Device
from models.google_sheet import GoogleSheetTrigger
from db.base import Base

def compare_schemas():
    db_url = os.getenv("DATABASE_URL")
    if "?sslmode=require" not in db_url:
        db_url += "?sslmode=require"
    
    engine = create_engine(db_url)
    inspector = inspect(engine)
    
    # Tables to check
    table_model_map = {
        'businesses': BusiUser,
        'devices': Device,
        'google_sheet_triggers': GoogleSheetTrigger
    }
    
    for table_name, model in table_model_map.items():
        print(f"\n--- Checking Table: {table_name} ---")
        
        # Get actual columns from DB
        try:
            db_columns = {c['name']: c for c in inspector.get_columns(table_name)}
        except Exception as e:
            print(f"ERROR: Could not get columns for {table_name}: {e}")
            continue
            
        # Get expected columns from Model
        model_columns = model.__table__.columns.keys()
        
        missing = []
        for col in model_columns:
            if col not in db_columns:
                missing.append(col)
        
        if missing:
            print(f"MISSING: MISSING COLUMNS in DB: {', '.join(missing)}")
        else:
            print("SUCCESS: All model columns found in DB.")
            
        # Check for type mismatches (especially UUID vs String)
        for col in model_columns:
            if col in db_columns:
                db_type = str(db_columns[col]['type']).upper()
                # Simplified check
                if 'UUID' in str(model.__table__.columns[col].type).upper() and 'VARCHAR' in db_type:
                    print(f"WARNING: TYPE MISMATCH: {col} is Model:UUID vs DB:{db_type}")
                elif 'VARCHAR' in str(model.__table__.columns[col].type).upper() and 'UUID' in db_type:
                     print(f"WARNING: TYPE MISMATCH: {col} is Model:VARCHAR vs DB:{db_type}")

if __name__ == "__main__":
    compare_schemas()
