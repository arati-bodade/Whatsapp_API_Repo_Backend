#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.abspath(__file__))

from db.base import engine
from sqlalchemy import text

def fix_group_contacts_foreign_key():
    """Fix the foreign key constraint to point to the correct table"""
    
    with engine.connect() as conn:
        try:
            # Start transaction
            trans = conn.begin()
            
            print("Dropping incorrect foreign key constraint...")
            conn.execute(text("ALTER TABLE group_contacts DROP CONSTRAINT group_contacts_group_id_fkey"))
            
            print("Adding correct foreign key constraint...")
            conn.execute(text("""
                ALTER TABLE group_contacts 
                ADD CONSTRAINT group_contacts_group_id_fkey 
                FOREIGN KEY (group_id) REFERENCES contact_groups(group_id)
            """))
            
            # Commit the transaction
            trans.commit()
            print("✅ Foreign key constraint fixed successfully!")
            
            # Verify the fix
            result = conn.execute(text("""
                SELECT 
                    tc.constraint_name, 
                    tc.table_name, 
                    kcu.column_name, 
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name 
                FROM information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY' 
                    AND tc.table_name = 'group_contacts'
                    AND kcu.column_name = 'group_id'
            """))
            
            constraint = result.fetchone()
            if constraint:
                print(f"Verified: {constraint[1]}.{constraint[2]} -> {constraint[3]}.{constraint[4]}")
            else:
                print("❌ Could not verify the constraint")
                
        except Exception as e:
            trans.rollback()
            print(f"❌ Error fixing foreign key: {e}")
            raise

if __name__ == "__main__":
    fix_group_contacts_foreign_key()
