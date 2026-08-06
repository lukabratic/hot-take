"""initial_schema

Revision ID: 0001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clerk_id", sa.String(length=255), nullable=False),
        sa.Column("username", sa.String(length=80), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("avatar_url", sa.String(length=500), nullable=True),
        sa.Column("current_streak", sa.Integer(), server_default="0"),
        sa.Column("longest_streak", sa.Integer(), server_default="0"),
        sa.Column("last_daily_completed", sa.Date(), nullable=True),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("clerk_id"),
        sa.UniqueConstraint("username"),
    )

    # Create players table
    op.create_table(
        "players",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("position", sa.String(length=10), nullable=False),
        sa.Column("era", sa.String(length=50), nullable=True),
        sa.Column("career_stats", sa.JSON(), nullable=False),
        sa.Column("peak_stats", sa.JSON(), nullable=False),
        sa.Column("playoff_stats", sa.JSON(), nullable=True),
        sa.Column("all_nba_selections", sa.Integer(), server_default="0"),
        sa.Column("mvp_vote_shares", sa.Float(), server_default="0.0"),
        sa.Column("championships", sa.Integer(), server_default="0"),
        sa.Column("all_star_selections", sa.Integer(), server_default="0"),
        sa.Column("hof_rank", sa.Integer(), nullable=True),
        sa.Column("bbref_id", sa.String(length=50), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("bbref_id"),
    )

    # Create rolls table
    op.create_table(
        "rolls",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("position", sa.String(length=20), nullable=False),
        sa.Column("theme_modifier", sa.String(length=50), nullable=False),
        sa.Column("daily_date", sa.Date(), nullable=True),
        sa.Column("mode", sa.String(length=20), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("daily_date"),
    )

    # Create roll_players table
    op.create_table(
        "roll_players",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("roll_id", sa.Integer(), nullable=False),
        sa.Column("player_id", sa.Integer(), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["roll_id"], ["rolls.id"]),
        sa.ForeignKeyConstraint(["player_id"], ["players.id"]),
    )

    # Create rankings table
    op.create_table(
        "rankings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("roll_id", sa.Integer(), nullable=False),
        sa.Column("rubric", sa.String(length=20), nullable=False),
        sa.Column("player_order", sa.JSON(), nullable=False),
        sa.Column("kendall_tau_distance", sa.Integer(), nullable=False),
        sa.Column("letter_grade", sa.String(length=1), nullable=False),
        sa.Column("mode", sa.String(length=20), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["roll_id"], ["rolls.id"]),
        sa.UniqueConstraint("user_id", "roll_id", name="uq_user_daily_ranking"),
    )

    # Create community_aggregates table
    op.create_table(
        "community_aggregates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("roll_id", sa.Integer(), nullable=False),
        sa.Column("player_id", sa.Integer(), nullable=False),
        sa.Column("slot_position", sa.Integer(), nullable=False),
        sa.Column("count", sa.Integer(), server_default="0"),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["roll_id"], ["rolls.id"]),
        sa.ForeignKeyConstraint(["player_id"], ["players.id"]),
        sa.UniqueConstraint("roll_id", "player_id", "slot_position", name="uq_community_agg"),
    )

    # Create debate_sessions table
    op.create_table(
        "debate_sessions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("roll_id", sa.Integer(), nullable=False),
        sa.Column("creator_id", sa.UUID(), nullable=False),
        sa.Column("opponent_id", sa.UUID(), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="waiting"),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["roll_id"], ["rolls.id"]),
        sa.ForeignKeyConstraint(["creator_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["opponent_id"], ["users.id"]),
    )

    # Create friendships table
    op.create_table(
        "friendships",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("friend_id", sa.UUID(), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["friend_id"], ["users.id"]),
        sa.UniqueConstraint("user_id", "friend_id", name="uq_friendship"),
        sa.CheckConstraint("user_id != friend_id", name="ck_no_self_friend"),
    )


def downgrade() -> None:
    op.drop_table("friendships")
    op.drop_table("debate_sessions")
    op.drop_table("community_aggregates")
    op.drop_table("rankings")
    op.drop_table("roll_players")
    op.drop_table("rolls")
    op.drop_table("players")
    op.drop_table("users")
