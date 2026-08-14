"""add is hidden to reviews

Revision ID: 91683f563ee5
Revises: 843f9c4717ea
Create Date: 2026-08-14 23:22:18.807405

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "91683f563ee5"
down_revision: Union[str, None] = "843f9c4717ea"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "reviews",
        sa.Column(
            "is_hidden",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade() -> None:
    op.drop_column("reviews", "is_hidden")