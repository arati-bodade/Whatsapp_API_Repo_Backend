"""Add last_processed_row to google_sheet_triggers

Revision ID: 010_add_last_processed_row
Revises: 009_fix_trigger_schema_complete
Create Date: 2026-01-30 00:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '010_add_last_processed_row'
down_revision = '009_fix_trigger_schema_complete'
branch_labels = None
depends_on = None


def upgrade():
    """Add last_processed_row column to google_sheet_triggers"""
    
    # Check if column exists first
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    
    existing_columns = [col['name'] for col in inspector.get_columns('google_sheet_triggers')]
    
    if 'last_processed_row' not in existing_columns:
        # Add the missing column
        op.add_column('google_sheet_triggers', sa.Column('last_processed_row', sa.Integer(), nullable=False, server_default='0'))
        
        # Update existing rows to have default value
        op.execute("""
            UPDATE google_sheet_triggers 
            SET last_processed_row = 0 
            WHERE last_processed_row IS NULL
        """)
        
        print("✅ Added last_processed_row column to google_sheet_triggers")
    else:
        print("✅ last_processed_row column already exists")


def downgrade():
    """Remove last_processed_row column"""
    
    op.drop_column('google_sheet_triggers', 'last_processed_row')
    print("✅ Removed last_processed_row column")
