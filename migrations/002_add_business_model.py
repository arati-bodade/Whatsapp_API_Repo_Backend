"""
Add Business Model Migration

Creates businesses table for business owners/sub-users.
Establishes foreign key relationship with users table.
"""

from sqlalchemy import create_engine, text
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import settings


def upgrade():
    """Create businesses table."""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as connection:
        # Create businesses table
        sql = """
            CREATE TABLE IF NOT EXISTS businesses (
                busi_user_id UUID PRIMARY KEY,
                role VARCHAR(50) NOT NULL DEFAULT 'business_owner',
                status VARCHAR(20) NOT NULL DEFAULT 'active',
                parent_reseller_id UUID NOT NULL REFERENCES resellers(user_id),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE,
                
                -- Profile fields
                name VARCHAR(255) NOT NULL,
                username VARCHAR(100) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                phone VARCHAR(20) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                
                -- Business fields
                business_name VARCHAR(255) NOT NULL,
                business_description TEXT,
                erp_system VARCHAR(100),
                gstin VARCHAR(15) UNIQUE,
                
                -- Address fields
                full_address TEXT,
                pincode VARCHAR(10),
                country VARCHAR(100),
                
                -- Wallet fields (different from users)
                credits_allocated INTEGER DEFAULT 0,
                credits_used INTEGER DEFAULT 0,
                credits_remaining INTEGER DEFAULT 0,
                
                -- WhatsApp mode
                whatsapp_mode VARCHAR(20) DEFAULT 'unofficial'
            );
        """
        connection.execute(text(sql))
        
        # Create indexes for better performance
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_businesses_username ON businesses(username);"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_businesses_email ON businesses(email);"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_businesses_parent_reseller ON businesses(parent_reseller_id);"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_businesses_role ON businesses(role);"))
        
        connection.commit()
        print("Businesses table created successfully")


def downgrade():
    """Remove businesses table (rollback)."""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as connection:
        connection.execute(text("DROP TABLE IF EXISTS businesses;"))
        connection.commit()
        print("Businesses table dropped (rollback)")
