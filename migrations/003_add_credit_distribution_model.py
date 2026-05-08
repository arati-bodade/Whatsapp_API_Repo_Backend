"""
Add Credit Distribution Model Migration

Creates credit_distributions table for tracking credit transfers
from resellers to business owners.
"""

from sqlalchemy import create_engine, text
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import settings


def upgrade():
    """Create credit_distributions table."""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as connection:
        # Create credit_distributions table
        sql = """
            CREATE TABLE IF NOT EXISTS credit_distributions (
                distribution_id VARCHAR(50) PRIMARY KEY,
                from_reseller_id UUID NOT NULL REFERENCES resellers(user_id),
                to_business_user_id UUID NOT NULL REFERENCES businesses(busi_user_id),
                credits_shared INTEGER NOT NULL,
                shared_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """
        connection.execute(text(sql))
        
        # Create indexes for better performance
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_credit_distributions_from_reseller ON credit_distributions(from_reseller_id);"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_credit_distributions_to_business ON credit_distributions(to_business_user_id);"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_credit_distributions_shared_at ON credit_distributions(shared_at);"))
        
        connection.commit()
        print("Credit distributions table created successfully")


def downgrade():
    """Remove credit_distributions table (rollback)."""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as connection:
        connection.execute(text("DROP TABLE IF EXISTS credit_distributions;"))
        connection.commit()
        print("Credit distributions table dropped (rollback)")
