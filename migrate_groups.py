#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db.base import engine
from sqlalchemy import text

def migrate_groups_to_contact_groups():
    """Migrate groups from groups table to contact_groups table"""
    
    with engine.connect() as conn:
        try:
            # Start transaction
            trans = conn.begin()
            
            print("Checking for groups that exist in 'groups' table but not in 'contact_groups'...")
            result = conn.execute(text("""
                SELECT g.group_id, g.name, g.busi_user_id, g.description, g.created_at
                FROM groups g
                LEFT JOIN contact_groups cg ON g.group_id = cg.group_id
                WHERE cg.group_id IS NULL
            """))
            
            missing_groups = result.fetchall()
            
            if missing_groups:
                print(f"Found {len(missing_groups)} groups to migrate:")
                for row in missing_groups:
                    print(f"  - {row[0]}: {row[1]} (User: {row[2]})")
                
                # Migrate these groups to contact_groups
                print("\nMigrating groups to contact_groups table...")
                for row in missing_groups:
                    conn.execute(text("""
                        INSERT INTO contact_groups (group_id, user_id, name, description, created_at)
                        VALUES (:group_id, :user_id, :name, :description, :created_at)
                    """), {
                        'group_id': row[0],
                        'user_id': row[2],  # busi_user_id -> user_id
                        'name': row[1],
                        'description': row[3],
                        'created_at': row[4]
                    })
                
                print(f"Migrated {len(missing_groups)} groups")
                
            else:
                print("All groups already exist in contact_groups")
            
            # Commit the transaction
            trans.commit()
            print("✅ Migration completed successfully!")
            
        except Exception as e:
            trans.rollback()
            print(f"❌ Error during migration: {e}")
            raise

if __name__ == "__main__":
    migrate_groups_to_contact_groups()
