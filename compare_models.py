#!/usr/bin/env python3

def compare_models():
    """Compare GoogleSheet model with a working model"""
    
    try:
        from models.google_sheet import GoogleSheet
        from models.busi_user import BusiUser
        from db.base import Base
        
        print("Comparing GoogleSheet with BusiUser model...")
        
        # Check BusiUser (working model)
        print(f"\nBusiUser:")
        print(f"  - __tablename__: {BusiUser.__tablename__}")
        print(f"  - In Base.metadata: {'businesses' in Base.metadata.tables}")
        print(f"  - Table object: {BusiUser.__table__}")
        print(f"  - Table name in table object: {BusiUser.__table__.name}")
        
        # Check GoogleSheet (problematic model)
        print(f"\nGoogleSheet:")
        print(f"  - __tablename__: {GoogleSheet.__tablename__}")
        print(f"  - In Base.metadata: {'google_sheets' in Base.metadata.tables}")
        print(f"  - Table object: {GoogleSheet.__table__}")
        print(f"  - Table name in table object: {GoogleSheet.__table__.name}")
        
        # Try to manually register GoogleSheet
        print(f"\nTrying to manually register GoogleSheet...")
        try:
            Base.metadata._add_table(GoogleSheet.__table__.name, GoogleSheet.__table__)
            print("✅ Manual registration successful")
            print(f"  - Now in Base.metadata: {'google_sheets' in Base.metadata.tables}")
        except Exception as e:
            print(f"❌ Manual registration failed: {e}")
        
        # Check foreign key definitions
        print(f"\nChecking foreign keys...")
        busi_user_fks = [str(fk) for fk in BusiUser.__table__.foreign_keys]
        google_sheet_fks = [str(fk) for fk in GoogleSheet.__table__.foreign_keys]
        
        print(f"BusiUser foreign keys: {busi_user_fks}")
        print(f"GoogleSheet foreign keys: {google_sheet_fks}")
        
        # Check if there are any import issues with the foreign key reference
        print(f"\nChecking foreign key references...")
        for fk in GoogleSheet.__table__.foreign_keys:
            print(f"  - FK: {fk}")
            print(f"    - Target table: {fk.column.table}")
            print(f"    - Target column: {fk.column}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    compare_models()
