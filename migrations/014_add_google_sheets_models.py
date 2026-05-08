"""Add Google Sheets integration models

Revision ID: 014_add_google_sheets_models
Revises: 013_add_timestamps
Create Date: 2024-01-28 11:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '014_add_google_sheets_models'
down_revision = '013_add_timestamps'
branch_labels = None
depends_on = None


def upgrade():
    # Create enum types
    op.execute("CREATE TYPE sheetstatus AS ENUM ('active', 'paused', 'error')")
    op.execute("CREATE TYPE triggertype AS ENUM ('new_row', 'update_row', 'time')")
    op.execute("CREATE TYPE triggerhistorystatus AS ENUM ('sent', 'failed')")

    # Create google_sheets table
    op.create_table('google_sheets',
        sa.Column('sheet_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sheet_name', sa.String(), nullable=False),
        sa.Column('spreadsheet_id', sa.String(), nullable=False),
        sa.Column('status', sa.Enum('active', 'paused', 'error', name='sheetstatus'), nullable=True),
        sa.Column('rows_count', sa.Integer(), nullable=True),
        sa.Column('last_synced_at', sa.DateTime(), nullable=True),
        sa.Column('connected_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['businesses.busi_user_id'], ),
        sa.PrimaryKeyConstraint('sheet_id')
    )
    op.create_index(op.f('ix_google_sheets_sheet_id'), 'google_sheets', ['sheet_id'], unique=False)

    # Create google_sheet_triggers table
    op.create_table('google_sheet_triggers',
        sa.Column('trigger_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sheet_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('trigger_type', sa.Enum('new_row', 'update_row', 'time', name='triggertype'), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), nullable=True),
        sa.Column('last_triggered_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['device_id'], ['devices.device_id'], ),
        sa.ForeignKeyConstraint(['sheet_id'], ['google_sheets.sheet_id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['businesses.busi_user_id'], ),
        sa.PrimaryKeyConstraint('trigger_id')
    )
    op.create_index(op.f('ix_google_sheet_triggers_trigger_id'), 'google_sheet_triggers', ['trigger_id'], unique=False)

    # Create google_sheet_trigger_history table
    op.create_table('google_sheet_trigger_history',
        sa.Column('history_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sheet_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('trigger_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('row_number', sa.Integer(), nullable=False),
        sa.Column('phone', sa.String(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('status', sa.Enum('sent', 'failed', name='triggerhistorystatus'), nullable=False),
        sa.Column('executed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['device_id'], ['devices.device_id'], ),
        sa.ForeignKeyConstraint(['sheet_id'], ['google_sheets.sheet_id'], ),
        sa.ForeignKeyConstraint(['trigger_id'], ['google_sheet_triggers.trigger_id'], ),
        sa.PrimaryKeyConstraint('history_id')
    )
    op.create_index(op.f('ix_google_sheet_trigger_history_history_id'), 'google_sheet_trigger_history', ['history_id'], unique=False)

    # Set default values
    op.execute("UPDATE google_sheets SET status = 'active' WHERE status IS NULL")
    op.execute("UPDATE google_sheets SET rows_count = 0 WHERE rows_count IS NULL")
    op.execute("UPDATE google_sheets SET connected_at = NOW() WHERE connected_at IS NULL")
    op.execute("UPDATE google_sheet_triggers SET is_enabled = true WHERE is_enabled IS NULL")
    op.execute("UPDATE google_sheet_triggers SET created_at = NOW() WHERE created_at IS NULL")
    op.execute("UPDATE google_sheet_trigger_history SET executed_at = NOW() WHERE executed_at IS NULL")

    # Make columns NOT NULL after setting defaults
    op.alter_column('google_sheets', 'status', nullable=False)
    op.alter_column('google_sheets', 'rows_count', nullable=False)
    op.alter_column('google_sheets', 'connected_at', nullable=False)
    op.alter_column('google_sheet_triggers', 'is_enabled', nullable=False)
    op.alter_column('google_sheet_triggers', 'created_at', nullable=False)
    op.alter_column('google_sheet_trigger_history', 'executed_at', nullable=False)


def downgrade():
    # Drop tables
    op.drop_index(op.f('ix_google_sheet_trigger_history_history_id'), table_name='google_sheet_trigger_history')
    op.drop_table('google_sheet_trigger_history')
    op.drop_index(op.f('ix_google_sheet_triggers_trigger_id'), table_name='google_sheet_triggers')
    op.drop_table('google_sheet_triggers')
    op.drop_index(op.f('ix_google_sheets_sheet_id'), table_name='google_sheets')
    op.drop_table('google_sheets')

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS triggerhistorystatus")
    op.execute("DROP TYPE IF EXISTS triggertype")
    op.execute("DROP TYPE IF EXISTS sheetstatus")
