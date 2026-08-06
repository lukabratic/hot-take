"""add_category_columns

Revision ID: 0002
Revises: 0001
Create Date: 2024-02-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add team and conference columns to players table
    op.add_column("players", sa.Column("team", sa.String(length=50), nullable=True))
    op.add_column("players", sa.Column("conference", sa.String(length=10), nullable=True))

    # Add category_type and category_value columns to rolls table
    op.add_column("rolls", sa.Column("category_type", sa.String(length=20), nullable=True))
    op.add_column("rolls", sa.Column("category_value", sa.String(length=50), nullable=True))


def downgrade() -> None:
    op.drop_column("rolls", "category_value")
    op.drop_column("rolls", "category_type")
    op.drop_column("players", "conference")
    op.drop_column("players", "team")
