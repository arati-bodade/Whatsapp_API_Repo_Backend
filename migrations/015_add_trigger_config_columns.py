"""Add additional columns for Google Sheets trigger configuration

Revision ID: 015_add_trigger_config_columns
Revises: 014_add_google_sheets_models
Create Date: 2024-01-28 11:35:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '015_add_trigger_config_columns'
down_revision = '014_add_google_sheets_models'
branch_labels = None
depends_on = None


def upgrade():
    # Add additional columns for trigger configuration
    op.add_column('google_sheet_triggers', sa.Column('message_template', sa.Text(), nullable=True))
    op.add_column('google_sheet_triggers', sa.Column('phone_column', sa.String(), nullable=True))
    op.add_column('google_sheet_triggers', sa.Column('trigger_column', sa.String(), nullable=True))
    op.add_column('google_sheet_triggers', sa.Column('trigger_value', sa.String(), nullable=True))
    op.add_column('google_sheet_triggers', sa.Column('webhook_url', sa.String(), nullable=True))
    op.add_column('google_sheet_triggers', sa.Column('polling_interval', sa.Integer(), nullable=True))
    op.add_column('google_sheet_triggers', sa.Column('last_processed_row', sa.Integer(), nullable=True))

    # Set default values
    op.execute("UPDATE google_sheet_triggers SET message_template = 'Hello {name}' WHERE message_template IS NULL")
    op.execute("UPDATE google_sheet_triggers SET phone_column = 'A' WHERE phone_column IS NULL")
    op.execute("UPDATE google_sheet_triggers SET polling_interval = 5 WHERE polling_interval IS NULL")
    op.execute("UPDATE google_sheet_triggers SET last_processed_row = 0 WHERE last_processed_row IS NULL")

    # Make some columns NOT NULL after setting defaults
    op.alter_column('google_sheet_triggers', 'message_template', nullable=False)
    op.alter_column('google_sheet_triggers', 'phone_column', nullable=False)
    op.alter_column('google_sheet_triggers', 'polling_interval', nullable=False)
    op.alter_column('google_sheet_triggers', 'last_processed_row', nullable=False)


def downgrade():
    # Remove added columns
    op.drop_column('google_sheet_triggers', 'last_processed_row')
    op.drop_column('google_sheet_triggers', 'polling_interval')
    op.drop_column('google_sheet_triggers', 'webhook_url')
    op.drop_column('google_sheet_triggers', 'trigger_value')
    op.drop_column('google_sheet_triggers', 'trigger_column')
    op.drop_column('google_sheet_triggers', 'phone_column')
    op.drop_column('google_sheet_triggers', 'message_template')
