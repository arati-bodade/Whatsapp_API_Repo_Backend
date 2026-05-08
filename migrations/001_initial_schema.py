"""
Initial Schema Migration

Creates initial database schema for users table.
This represents starting point of database.
"""

from sqlalchemy import create_engine, text
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import settings


def upgrade():
    """Create initial users table schema."""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as connection:
        # Create users table
        sql = """
            CREATE TABLE IF NOT EXISTS users (
                user_id UUID PRIMARY KEY,
                role VARCHAR(50) NOT NULL DEFAULT 'reseller',
                status VARCHAR(20) NOT NULL DEFAULT 'active',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE,
                
                -- Profile fields
                name VARCHAR(255) NOT NULL,
                username VARCHAR(100) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                phone VARCHAR(20) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                
                -- Business fields
                business_name VARCHAR(255),
                business_description TEXT,
                erp_system VARCHAR(100),
                gstin VARCHAR(15) UNIQUE,
                
                -- Address fields
                full_address TEXT,
                pincode VARCHAR(10),
                country VARCHAR(100),
                
                -- Bank fields
                bank_name VARCHAR(255),
                
                -- Wallet fields
                total_credits INTEGER DEFAULT 0,
                available_credits INTEGER DEFAULT 0,
                used_credits INTEGER DEFAULT 0
            );
        """
        connection.execute(text(sql))
        
        # Create indexes for better performance
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);"))
        
        connection.commit()
        print("Initial users table created successfully")


def downgrade():
    """Remove users table (rollback)."""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as connection:
        connection.execute(text("DROP TABLE IF EXISTS users;"))
        connection.commit()
        print("Users table dropped (rollback)")
