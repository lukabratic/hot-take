"""Make rankings.user_id nullable for anonymous play.

Revision ID: 0003
Revises: 0002
Create Date: 2024-03-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: str = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("rankings", "user_id", existing_type=sa.UUID(), nullable=True)
    # Drop the unique constraint that assumes user_id is always present
    op.drop_constraint("uq_user_daily_ranking", "rankings", type_="unique")
    # Re-create it as a partial unique index (only for authenticated submissions)
    op.execute(
        "CREATE UNIQUE INDEX uq_user_daily_ranking ON rankings (user_id, roll_id) WHERE user_id IS NOT NULL"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_user_daily_ranking")
    op.create_unique_constraint("uq_user_daily_ranking", "rankings", ["user_id", "roll_id"])
    op.alter_column("rankings", "user_id", existing_type=sa.UUID(), nullable=False)
