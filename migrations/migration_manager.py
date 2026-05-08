"""
Migration Manager

Utility to run database migrations in order.
Tracks applied migrations to avoid re-running them.
"""

from sqlalchemy import create_engine, text
import sys
import os
import glob

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import settings


class MigrationManager:
    def __init__(self):
        self.engine = create_engine(settings.DATABASE_URL)
        self.migrations_dir = "migrations"
        
    def ensure_migration_table(self):
        """Create migrations table to track applied migrations."""
        with self.engine.connect() as connection:
            sql = """
                CREATE TABLE IF NOT EXISTS migrations (
                    id SERIAL PRIMARY KEY,
                    filename VARCHAR(255) UNIQUE NOT NULL,
                    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """
            connection.execute(text(sql))
            connection.commit()
    
    def get_applied_migrations(self):
        """Get list of already applied migrations."""
        with self.engine.connect() as connection:
            result = connection.execute(text("SELECT filename FROM migrations ORDER BY filename;"))
            return [row[0] for row in result.fetchall()]
    
    def get_pending_migrations(self):
        """Get list of pending migrations to be applied."""
        migration_files = sorted(glob.glob(f"{self.migrations_dir}/*.py"))
        migration_names = [os.path.basename(f) for f in migration_files]
        
        # Filter out __init__.py and migration_manager.py
        migration_names = [name for name in migration_names 
                         if name.startswith(('0', '1', '2', '3', '4', '5', '6', '7', '8', '9'))]
        
        applied_migrations = self.get_applied_migrations()
        return [name for name in migration_names if name not in applied_migrations]
    
    def apply_migration(self, migration_file):
        """Apply a single migration."""
        try:
            # Import the migration module
            module_name = migration_file.replace('.py', '')
            migration_module = __import__(f"{self.migrations_dir}.{module_name}", fromlist=['upgrade'])
            
            # Run upgrade
            migration_module.upgrade()
            
            # Record migration as applied
            with self.engine.connect() as connection:
                connection.execute(text(
                    "INSERT INTO migrations (filename) VALUES (:filename)"
                ), {"filename": migration_file})
                connection.commit()
            
            print(f"✅ Applied migration: {migration_file}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to apply migration {migration_file}: {e}")
            return False
    
    def run_migrations(self):
        """Run all pending migrations."""
        print("🔄 Starting database migrations...")
        
        self.ensure_migration_table()
        pending_migrations = self.get_pending_migrations()
        
        if not pending_migrations:
            print("✅ No pending migrations to apply")
            return
        
        print(f"📋 Found {len(pending_migrations)} pending migration(s):")
        for migration in pending_migrations:
            print(f"   - {migration}")
        
        print("\n🚀 Applying migrations...")
        
        for migration in pending_migrations:
            if not self.apply_migration(migration):
                print(f"⚠️ Migration stopped due to error at {migration}")
                break
        
        print("✅ Migration process completed")


def run_migrations():
    """Convenience function to run migrations."""
    manager = MigrationManager()
    manager.run_migrations()


if __name__ == "__main__":
    run_migrations()
