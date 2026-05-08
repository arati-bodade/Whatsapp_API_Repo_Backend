#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db.base import engine
from sqlalchemy import text

def check_group_tables():
    """Check what group-related tables exist in the database"""
    
    with engine.connect() as conn:
        # Check for group-related tables
        result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name LIKE '%group%'"))
        tables = [row[0] for row in result]
        print('Tables containing "group":', tables)
        
        # Check the actual foreign key constraints
        if 'group_contacts' in tables:
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
            """))
            
            constraints = result.fetchall()
            print('\nForeign key constraints for group_contacts:')
            for constraint in constraints:
                print(f'  {constraint[0]}: {constraint[1]}.{constraint[2]} -> {constraint[3]}.{constraint[4]}')
        
        # Check if groups table exists
        result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'groups'"))
        groups_table_exists = result.fetchone() is not None
        print(f'\n"groups" table exists: {groups_table_exists}')
        
        # Check if contact_groups table exists
        result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'contact_groups'"))
        contact_groups_table_exists = result.fetchone() is not None
        print(f'"contact_groups" table exists: {contact_groups_table_exists}')

if __name__ == "__main__":
    check_group_tables()
