"""Fix google_sheet_triggers.sheet_id from VARCHAR to UUID

Revision ID: 017_fix_google_sheet_triggers_sheet_id_uuid
Revises: 016_fix_google_sheet_device_relationship
Create Date: 2025-02-02 12:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '017_fix_google_sheet_triggers_sheet_id_uuid'
down_revision = '016_fix_google_sheet_device_relationship'
branch_labels = None
depends_on = None


def upgrade():
    """
    Convert google_sheet_triggers.sheet_id from VARCHAR to UUID safely.
    This fixes the "operator does not exist: character varying = uuid" error.
    """
    
    # Step 1: Check if column is already UUID (skip if already fixed)
    conn = op.get_bind()
    result = conn.execute(sa.text("""
        SELECT data_type 
        FROM information_schema.columns 
        WHERE table_name = 'google_sheet_triggers' 
        AND column_name = 'sheet_id'
    """))
    current_type = result.scalar()
    
    if current_type == 'uuid':
        print("sheet_id is already UUID type - skipping migration")
        return
    
    # Step 2: Validate existing data (ensure all values are valid UUIDs)
    conn.execute(sa.text("""
        -- Check for invalid UUIDs before conversion
        SELECT COUNT(*) 
        FROM google_sheet_triggers 
        WHERE sheet_id IS NOT NULL 
        AND sheet_id !~ '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
    """))
    
    invalid_count = result.scalar() if hasattr(result, 'scalar') else 0
    
    if invalid_count > 0:
        raise Exception(f"Found {invalid_count} invalid UUID values in sheet_id column. Please fix data before migration.")
    
    # Step 3: Convert VARCHAR to UUID using PostgreSQL type casting
    op.execute("""
        ALTER TABLE google_sheet_triggers 
        ALTER COLUMN sheet_id 
        TYPE UUID USING sheet_id::UUID
    """)
    
    print("✅ Successfully converted google_sheet_triggers.sheet_id to UUID")


def downgrade():
    """
    Revert UUID back to VARCHAR (if needed)
    """
    op.execute("""
        ALTER TABLE google_sheet_triggers 
        ALTER COLUMN sheet_id 
        TYPE VARCHAR USING sheet_id::TEXT
    """)
    
    print("⚠️  Reverted google_sheet_triggers.sheet_id back to VARCHAR")
