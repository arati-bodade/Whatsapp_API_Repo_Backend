"""Fix GoogleSheet device relationship issue

Revision ID: 016_fix_google_sheet_device_relationship
Revises: 015_add_trigger_config_columns
Create Date: 2024-01-28 11:54:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '016_fix_google_sheet_device_relationship'
down_revision = '015_add_trigger_config_columns'
branch_labels = None
depends_on = None


def upgrade():
    # No changes needed - we removed the invalid relationship from the model
    # The database schema is already correct
    pass


def downgrade():
    # No changes needed for downgrade
    pass
