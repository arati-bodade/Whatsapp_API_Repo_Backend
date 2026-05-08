"""Add status_column to GoogleSheetTrigger

Revision ID: 008_add_trigger_status_column
Revises: 007_add_official_whatsapp_config
Create Date: 2026-01-29 23:41:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '008_add_trigger_status_column'
down_revision = '007_add_official_whatsapp_config'
branch_labels = None
depends_on = None


def upgrade():
    """Add status_column and last_processed_row to google_sheet_triggers"""
    
    # Add status_column with default value
    op.add_column('google_sheet_triggers', sa.Column('status_column', sa.String(), nullable=False, server_default='Status'))
    
    # Add last_processed_row for tracking
    op.add_column('google_sheet_triggers', sa.Column('last_processed_row', sa.Integer(), nullable=False, server_default='0'))
    
    # Update existing triggers to have default values
    op.execute("""
        UPDATE google_sheet_triggers 
        SET status_column = 'Status', last_processed_row = 0 
        WHERE status_column IS NULL OR last_processed_row IS NULL
    """)


def downgrade():
    """Remove status_column and last_processed_row from google_sheet_triggers"""
    
    op.drop_column('google_sheet_triggers', 'status_column')
    op.drop_column('google_sheet_triggers', 'last_processed_row')
