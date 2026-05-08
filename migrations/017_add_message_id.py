"""Add message_id to whatsapp_inbox

Revision ID: 017_add_message_id
Revises: 016_add_contact_name_chat_type
Create Date: 2026-02-11 15:55:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '017_add_message_id'
down_revision = '016_add_contact_name_chat_type'
branch_labels = None
depends_on = None


def upgrade():
    # Add message_id column to whatsapp_inbox table
    op.add_column('whatsapp_inbox', sa.Column('message_id', sa.String(), nullable=True))


def downgrade():
    # Remove message_id column from whatsapp_inbox table
    op.drop_column('whatsapp_inbox', 'message_id')
