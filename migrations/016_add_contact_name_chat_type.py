"""Add contact_name and chat_type to whatsapp_inbox

Revision ID: 016_add_contact_name_chat_type
Revises: 015_add_trigger_config_columns
Create Date: 2026-02-11 12:59:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '016_add_contact_name_chat_type'
down_revision = '015_add_trigger_config_columns'
branch_labels = None
depends_on = None

def upgrade():
    # Add contact_name column
    op.add_column('whatsapp_inbox', sa.Column('contact_name', sa.String(), nullable=True))
    
    # Add chat_type column with default 'individual'
    op.add_column('whatsapp_inbox', sa.Column('chat_type', sa.String(), nullable=True, server_default='individual'))
    
    # Update existing records to have chat_type = 'individual'
    op.execute("UPDATE whatsapp_inbox SET chat_type = 'individual' WHERE chat_type IS NULL")

def downgrade():
    # Remove columns
    op.drop_column('whatsapp_inbox', 'chat_type')
    op.drop_column('whatsapp_inbox', 'contact_name')
