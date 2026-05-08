"""Add Razorpay columns to payment_orders table

Revision ID: 022
Revises: 021_add_send_time_and_message_columns
Create Date: 2026-03-17 12:25:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '022_add_razorpay_columns_to_payment_orders'
down_revision = '021_add_send_time_and_message_columns'
branch_labels = None
depends_on = None


def upgrade():
    """Add Razorpay columns to payment_orders table"""
    # Add Razorpay columns if they don't exist
    op.add_column('payment_orders', sa.Column('razorpay_order_id', sa.String(100), nullable=True))
    op.add_column('payment_orders', sa.Column('razorpay_payment_id', sa.String(100), nullable=True))
    op.add_column('payment_orders', sa.Column('razorpay_signature', sa.String(255), nullable=True))


def downgrade():
    """Remove Razorpay columns from payment_orders table"""
    op.drop_column('payment_orders', 'razorpay_order_id')
    op.drop_column('payment_orders', 'razorpay_payment_id')
    op.drop_column('payment_orders', 'razorpay_signature')
