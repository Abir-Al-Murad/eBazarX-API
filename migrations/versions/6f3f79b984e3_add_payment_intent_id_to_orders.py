"""add_payment_intent_id_to_orders

Revision ID: 6f3f79b984e3
Revises: 91683f563ee5
Create Date: 2026-08-14 23:42:04.129917

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "6f3f79b984e3"
down_revision: Union[str, None] = "91683f563ee5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add the missing column
    op.add_column(
        'orders',
        sa.Column('payment_intent_id', sa.String(255), nullable=True)
    )


def downgrade() -> None:
    # Remove the column
    op.drop_column('orders', 'payment_intent_id')
