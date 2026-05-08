
import os
import sys
from sqlalchemy import create_engine, inspect, text
from db.base import Base
# Import all models to ensure they are in Base.metadata
from models.admin import MasterAdmin
from models.reseller import Reseller
from models.busi_user import BusiUser
from models.device import Device
from models.campaign import Campaign
from models.google_sheet import GoogleSheet, GoogleSheetTrigger
from models.whatsapp_messages import WhatsAppMessages
from models.message_usage import MessageUsageCreditLog

def audit_schema_mismatch():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not found in environment")
        return

    if "?sslmode=require" not in db_url:
        db_url += "?sslmode=require"
        
    engine = create_engine(db_url)
    inspector = inspect(engine)
    
    mismatches = []
    
    # Tables in models
    for table_name, table in Base.metadata.tables.items():
        if table_name not in inspector.get_table_names():
            print(f"MISSING TABLE: {table_name}")
            continue
            
        db_columns = {col['name']: col for col in inspector.get_columns(table_name)}
        
        for col_name, model_col in table.columns.items():
            if col_name not in db_columns:
                print(f"MISSING COLUMN: {table_name}.{col_name}")
                continue
                
            db_col = db_columns[col_name]
            db_type = str(db_col['type']).upper()
            model_type = str(model_col.type).upper()
            
            # Specifically looking for UUID vs VARCHAR mismatch
            if 'UUID' in model_type and 'VARCHAR' in db_type:
                mismatches.append({
                    'table': table_name,
                    'column': col_name,
                    'model_type': 'UUID',
                    'db_type': db_type
                })
            elif 'UUID' in model_type and 'UUID' not in db_type:
                 mismatches.append({
                    'table': table_name,
                    'column': col_name,
                    'model_type': 'UUID',
                    'db_type': db_type
                })

    if mismatches:
        print("\n--- UUID TYPE MISMATCHES FOUND ---")
        print(f"{'Table':<25} | {'Column':<25} | {'DB Type':<15} | {'Model Type':<15}")
        print("-" * 85)
        for m in mismatches:
            print(f"{m['table']:<25} | {m['column']:<25} | {m['db_type']:<15} | {m['model_type']:<15}")
    else:
        print("\nNo UUID type mismatches found!")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    audit_schema_mismatch()
