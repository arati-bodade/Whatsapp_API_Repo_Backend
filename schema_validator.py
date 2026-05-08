#!/usr/bin/env python3
"""
Schema validation utility to prevent future type mismatches
Run this on app startup to catch schema issues early
"""
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.engine import Engine

load_dotenv()

class SchemaValidator:
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        self.inspector = inspect(self.engine)
        self.errors = []
        self.warnings = []
    
    def validate_table_column_type(self, table_name: str, column_name: str, expected_type: str):
        """Validate that a column has the expected type"""
        try:
            columns = self.inspector.get_columns(table_name)
            column_info = next((col for col in columns if col['name'] == column_name), None)
            
            if not column_info:
                self.errors.append(f"❌ Column {table_name}.{column_name} not found")
                return False
            
            actual_type = str(column_info['type']).lower()
            expected_type_lower = expected_type.lower()
            
            if expected_type_lower not in actual_type:
                self.errors.append(
                    f"❌ Type mismatch: {table_name}.{column_name} is {actual_type}, expected {expected_type}"
                )
                return False
            
            print(f"✅ {table_name}.{column_name}: {actual_type}")
            return True
            
        except Exception as e:
            self.errors.append(f"❌ Error checking {table_name}.{column_name}: {e}")
            return False
    
    def validate_uuid_columns(self):
        """Validate all UUID columns that commonly cause issues"""
        uuid_checks = [
            ('google_sheet_triggers', 'sheet_id', 'UUID'),
            ('google_sheet_triggers', 'device_id', 'UUID'),
            ('google_sheet_triggers', 'trigger_id', 'UUID'),  # If using UUID
            ('google_sheets', 'id', 'UUID'),
            ('google_sheets', 'user_id', 'UUID'),
            ('google_sheets', 'device_id', 'UUID'),
        ]
        
        print("🔍 Validating UUID columns...")
        all_valid = True
        
        for table, column, expected_type in uuid_checks:
            try:
                # Check if table exists first
                if table not in self.inspector.get_table_names():
                    self.warnings.append(f"⚠️  Table {table} does not exist (skipping)")
                    continue
                
                if not self.validate_table_column_type(table, column, expected_type):
                    all_valid = False
            except Exception as e:
                self.warnings.append(f"⚠️  Could not validate {table}.{column}: {e}")
        
        return all_valid
    
    def validate_foreign_key_constraints(self):
        """Check that foreign key relationships are properly defined"""
        critical_fks = [
            ('google_sheet_triggers', 'sheet_id', 'google_sheets'),
            ('google_sheet_triggers', 'device_id', 'devices'),
        ]
        
        print("🔍 Validating foreign key constraints...")
        
        try:
            for table, fk_column, referenced_table in critical_fks:
                if table not in self.inspector.get_table_names():
                    continue
                
                fks = self.inspector.get_foreign_keys(table)
                fk_found = False
                
                for fk in fks:
                    if fk_column in fk['constrained_columns'] and referenced_table == fk['referred_table']:
                        fk_found = True
                        print(f"✅ FK {table}.{fk_column} -> {referenced_table}")
                        break
                
                if not fk_found:
                    self.warnings.append(f"⚠️  FK not found: {table}.{fk_column} -> {referenced_table}")
        
        except Exception as e:
            self.warnings.append(f"⚠️  Error checking foreign keys: {e}")
    
    def run_validation(self):
        """Run all schema validations"""
        print("🚀 Starting schema validation...")
        print("=" * 50)
        
        uuid_valid = self.validate_uuid_columns()
        self.validate_foreign_key_constraints()
        
        print("=" * 50)
        
        if self.errors:
            print("❌ SCHEMA ERRORS FOUND:")
            for error in self.errors:
                print(f"  {error}")
        
        if self.warnings:
            print("⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  {warning}")
        
        if not self.errors and not self.warnings:
            print("🎉 All schema validations passed!")
        
        return len(self.errors) == 0
    
    def close(self):
        """Close database connection"""
        self.engine.dispose()

def validate_schema_on_startup():
    """Function to call in FastAPI startup event"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("⚠️  No DATABASE_URL found - skipping schema validation")
        return True
    
    validator = SchemaValidator(database_url)
    try:
        is_valid = validator.run_validation()
        if not is_valid:
            print("❌ Schema validation failed - see errors above")
            print("💡 Consider running migrations to fix schema issues")
        return is_valid
    finally:
        validator.close()

if __name__ == "__main__":
    # Run as standalone script
    success = validate_schema_on_startup()
    sys.exit(0 if success else 1)
