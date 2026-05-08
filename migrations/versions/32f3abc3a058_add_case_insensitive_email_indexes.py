"""Add case-insensitive email indexes

Revision ID: 32f3abc3a058
Revises: 
Create Date: 2026-05-07 13:54:04.395482

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '32f3abc3a058'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add functional indexes for lower(email) if they don't exist
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_businesses_email_lower ON businesses (LOWER(email))")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_resellers_email_lower ON resellers (LOWER(email))")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_master_admins_email_lower ON master_admins (LOWER(email))")

def downgrade() -> None:
    # Drop functional indexes
    op.execute("DROP INDEX IF EXISTS ix_businesses_email_lower")
    op.execute("DROP INDEX IF EXISTS ix_resellers_email_lower")
    op.execute("DROP INDEX IF EXISTS ix_master_admins_email_lower")
