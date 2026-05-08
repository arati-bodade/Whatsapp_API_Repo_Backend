"""Fix GoogleSheetTrigger schema - Complete fix

Revision ID: 009_fix_trigger_schema_complete
Revises: 008_add_trigger_status_column
Create Date: 2026-01-30 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '009_fix_trigger_schema_complete'
down_revision = '008_add_trigger_status_column'
branch_labels = None
depends_on = None


def upgrade():
    """Complete fix for GoogleSheetTrigger schema"""
    
    # Check if columns exist, add if missing
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    
    # Get existing columns
    existing_columns = [col['name'] for col in inspector.get_columns('google_sheet_triggers')]
    
    # Add missing columns if they don't exist
    if 'phone_column' not in existing_columns:
        op.add_column('google_sheet_triggers', sa.Column('phone_column', sa.String(), nullable=False, server_default='phone'))
        print("✅ Added phone_column")
    
    if 'status_column' not in existing_columns:
        op.add_column('google_sheet_triggers', sa.Column('status_column', sa.String(), nullable=False, server_default='Status'))
        print("✅ Added status_column")
    
    if 'trigger_value' not in existing_columns:
        op.add_column('google_sheet_triggers', sa.Column('trigger_value', sa.String(), nullable=False, server_default='Send'))
        print("✅ Added trigger_value")
    
    if 'last_processed_row' not in existing_columns:
        op.add_column('google_sheet_triggers', sa.Column('last_processed_row', sa.Integer(), nullable=False, server_default='0'))
        print("✅ Added last_processed_row")
    
    # Update existing rows to have proper default values
    op.execute("""
        UPDATE google_sheet_triggers 
        SET 
            phone_column = COALESCE(NULLIF(phone_column, ''), 'phone'),
            status_column = COALESCE(NULLIF(status_column, ''), 'Status'),
            trigger_value = COALESCE(NULLIF(trigger_value, ''), 'Send'),
            last_processed_row = COALESCE(last_processed_row, 0)
        WHERE 
            phone_column IS NULL OR 
            status_column IS NULL OR 
            trigger_value IS NULL OR 
            last_processed_row IS NULL
    """)
    
    print("✅ Updated existing rows with default values")


def downgrade():
    """Remove the added columns"""
    
    # Remove columns in reverse order
    op.drop_column('google_sheet_triggers', 'last_processed_row')
    op.drop_column('google_sheet_triggers', 'trigger_value')
    op.drop_column('google_sheet_triggers', 'status_column')
    op.drop_column('google_sheet_triggers', 'phone_column')
    
    print("✅ Removed all trigger schema columns")
