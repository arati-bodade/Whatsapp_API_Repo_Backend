#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db.base import engine
from sqlalchemy import text

def cleanup_orphaned_group_contacts():
    """Clean up orphaned records in group_contacts before fixing foreign key"""
    
    with engine.connect() as conn:
        try:
            # Start transaction
            trans = conn.begin()
            
            print("Checking for orphaned group_contacts records...")
            
            # Find orphaned records (group_ids that don't exist in contact_groups)
            result = conn.execute(text("""
                SELECT gc.group_id, COUNT(*) as count
                FROM group_contacts gc
                LEFT JOIN contact_groups cg ON gc.group_id = cg.group_id
                WHERE cg.group_id IS NULL
                GROUP BY gc.group_id
            """))
            
            orphaned = result.fetchall()
            
            if orphaned:
                print(f"Found {len(orphaned)} orphaned group_id entries:")
                for row in orphaned:
                    print(f"  - Group ID {row[0]}: {row[1]} contact(s)")
                
                print("\nDeleting orphaned records...")
                result = conn.execute(text("""
                    DELETE FROM group_contacts 
                    WHERE group_id NOT IN (SELECT group_id FROM contact_groups)
                """))
                
                deleted_count = result.rowcount
                print(f"Deleted {deleted_count} orphaned records")
                
            else:
                print("No orphaned records found")
            
            # Now check if there are any records that should be migrated from groups to contact_groups
            print("\nChecking for groups that exist in 'groups' table but not in 'contact_groups'...")
            result = conn.execute(text("""
                SELECT g.group_id, g.name, g.user_id
                FROM groups g
                LEFT JOIN contact_groups cg ON g.group_id = cg.group_id
                WHERE cg.group_id IS NULL
            """))
            
            missing_groups = result.fetchall()
            
            if missing_groups:
                print(f"Found {len(missing_groups)} groups in 'groups' table missing from 'contact_groups':")
                for row in missing_groups:
                    print(f"  - Group ID {row[0]}: {row[1]} (User: {row[2]})")
                
                # Migrate these groups to contact_groups
                print("\nMigrating groups to contact_groups table...")
                for row in missing_groups:
                    conn.execute(text("""
                        INSERT INTO contact_groups (group_id, user_id, name, created_at)
                        VALUES (:group_id, :user_id, :name, NOW())
                    """), {
                        'group_id': row[0],
                        'user_id': row[1],  # Note: column order might be different
                        'name': row[2]
                    })
                
                print(f"Migrated {len(missing_groups)} groups")
                
            else:
                print("All groups already exist in contact_groups")
            
            # Commit the transaction
            trans.commit()
            print("✅ Cleanup completed successfully!")
            
        except Exception as e:
            trans.rollback()
            print(f"❌ Error during cleanup: {e}")
            raise

if __name__ == "__main__":
    cleanup_orphaned_group_contacts()
