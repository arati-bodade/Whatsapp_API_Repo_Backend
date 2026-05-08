"""Add WhatsApp messages table for enhanced CRM functionality

Revision ID: 018_add_whatsapp_messages_table
Revises: 017_add_message_id
Create Date: 2025-01-11 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '018_add_whatsapp_messages_table'
down_revision = '017_add_message_id'
branch_labels = None
depends_on = None


def upgrade():
    """Create the whatsapp_messages table with proper indexes"""
    
    # Create whatsapp_messages table
    op.create_table(
        'whatsapp_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('message_id', sa.String(length=255), nullable=False),
        sa.Column('remote_jid', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=20), nullable=False),
        sa.Column('contact_name', sa.String(length=255), nullable=True),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('message_type', sa.String(length=50), nullable=True, default='text'),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, default=sa.text('now()')),
        sa.Column('from_me', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_read', sa.Boolean(), nullable=False, default=False),
        sa.Column('chat_type', sa.String(length=20), nullable=True, default='individual'),
        sa.Column('media_url', sa.Text(), nullable=True),
        sa.Column('thumbnail_url', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True, default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, default=sa.text('now()')),
        sa.ForeignKeyConstraint(['device_id'], ['devices.device_id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('message_id')
    )
    
    # Create indexes for optimal performance
    op.create_index('idx_whatsapp_messages_message_id', 'whatsapp_messages', ['message_id'], unique=False)
    op.create_index('idx_whatsapp_messages_device_id', 'whatsapp_messages', ['device_id'], unique=False)
    op.create_index('idx_whatsapp_messages_phone', 'whatsapp_messages', ['phone'], unique=False)
    op.create_index('idx_whatsapp_messages_device_phone_time', 'whatsapp_messages', ['device_id', 'phone', 'timestamp'], unique=False)
    op.create_index('idx_whatsapp_messages_unread', 'whatsapp_messages', ['device_id', 'is_read', 'from_me', 'timestamp'], unique=False)
    op.create_index('idx_whatsapp_messages_chat_type', 'whatsapp_messages', ['chat_type'], unique=False)
    op.create_index('idx_whatsapp_messages_remote_jid', 'whatsapp_messages', ['remote_jid'], unique=False)


def downgrade():
    """Drop the whatsapp_messages table"""
    
    # Drop indexes first
    op.drop_index('idx_whatsapp_messages_remote_jid', table_name='whatsapp_messages')
    op.drop_index('idx_whatsapp_messages_chat_type', table_name='whatsapp_messages')
    op.drop_index('idx_whatsapp_messages_unread', table_name='whatsapp_messages')
    op.drop_index('idx_whatsapp_messages_device_phone_time', table_name='whatsapp_messages')
    op.drop_index('idx_whatsapp_messages_phone', table_name='whatsapp_messages')
    op.drop_index('idx_whatsapp_messages_device_id', table_name='whatsapp_messages')
    op.drop_index('idx_whatsapp_messages_message_id', table_name='whatsapp_messages')
    
    # Drop table
    op.drop_table('whatsapp_messages')
