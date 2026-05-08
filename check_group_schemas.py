#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db.base import engine
from sqlalchemy import text

def check_group_table_schemas():
    """Check the schema of groups and contact_groups tables"""
    
    with engine.connect() as conn:
        # Check groups table schema
        print("=== GROUPS table schema ===")
        result = conn.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'groups'
            ORDER BY ordinal_position
        """))
        
        groups_columns = []
        for row in result:
            groups_columns.append(row[0])
            print(f"  {row[0]}: {row[1]} (nullable: {row[2]})")
        
        print("\n=== CONTACT_GROUPS table schema ===")
        result = conn.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'contact_groups'
            ORDER BY ordinal_position
        """))
        
        contact_groups_columns = []
        for row in result:
            contact_groups_columns.append(row[0])
            print(f"  {row[0]}: {row[1]} (nullable: {row[2]})")
        
        # Check sample data
        print("\n=== Sample data from GROUPS ===")
        result = conn.execute(text("SELECT * FROM groups LIMIT 3"))
        for row in result:
            print(f"  {dict(row._mapping)}")
            
        print("\n=== Sample data from CONTACT_GROUPS ===")
        result = conn.execute(text("SELECT * FROM contact_groups LIMIT 3"))
        for row in result:
            print(f"  {dict(row._mapping)}")
            
        # Now try to migrate properly
        print("\n=== Migrating missing groups ===")
        if 'user_id' in groups_columns and 'user_id' in contact_groups_columns:
            result = conn.execute(text("""
                SELECT g.group_id, g.name, g.user_id
                FROM groups g
                LEFT JOIN contact_groups cg ON g.group_id = cg.group_id
                WHERE cg.group_id IS NULL
            """))
            
            missing_groups = result.fetchall()
            
            if missing_groups:
                print(f"Found {len(missing_groups)} groups to migrate")
                for row in missing_groups:
                    print(f"  - {row[0]}: {row[1]} (User: {row[2]})")
            else:
                print("No groups need migration")
        else:
            print("Column mismatch between tables")

if __name__ == "__main__":
    check_group_table_schemas()
