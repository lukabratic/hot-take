from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Date,
    ForeignKey,
    UniqueConstraint,
    CheckConstraint,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import relationship, DeclarativeBase
import uuid
from datetime import datetime, timezone


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clerk_id = Column(String(255), unique=True, nullable=False)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(255))
    avatar_url = Column(String(500))
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    last_daily_completed = Column(Date, nullable=True)
    created_at = Column(
        TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    rankings = relationship("Ranking", back_populates="user")
    created_debates = relationship(
        "DebateSession",
        foreign_keys="DebateSession.creator_id",
        back_populates="creator",
    )
    friendships = relationship(
        "Friendship",
        foreign_keys="Friendship.user_id",
        back_populates="user",
    )


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    position = Column(String(10), nullable=False)  # PG, SG, SF, PF, C
    era = Column(String(50))  # e.g., "1980s", "2000s", "2010s"
    career_stats = Column(JSON, nullable=False)  # {pts, reb, ast, stl, blk, per, bpm, vorp, ws}
    peak_stats = Column(JSON, nullable=False)  # Best single season stats
    playoff_stats = Column(JSON)  # Career playoff stats
    all_nba_selections = Column(Integer, default=0)
    mvp_vote_shares = Column(Float, default=0.0)
    championships = Column(Integer, default=0)
    all_star_selections = Column(Integer, default=0)
    hof_rank = Column(Integer, nullable=True)  # NULL if not in HOF
    team = Column(String(50), nullable=True)  # Primary franchise (e.g., "Lakers")
    conference = Column(String(10), nullable=True)  # "Eastern" or "Western"
    bbref_id = Column(String(50), unique=True, nullable=False)
    created_at = Column(
        TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    roll_players = relationship("RollPlayer", back_populates="player")


class Roll(Base):
    __tablename__ = "rolls"

    id = Column(Integer, primary_key=True)
    position = Column(String(20), nullable=False)
    theme_modifier = Column(String(50), nullable=False)
    category_type = Column(String(20), nullable=True)  # "position", "team", "decade", "conference"
    category_value = Column(String(50), nullable=True)  # Specific value (e.g., "Lakers", "1990s")
    daily_date = Column(Date, unique=True, nullable=True)  # NULL for non-daily
    mode = Column(String(20), nullable=False)  # daily, quickplay, hoopiq, debate
    created_at = Column(
        TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    roll_players = relationship("RollPlayer", back_populates="roll")
    rankings = relationship("Ranking", back_populates="roll")
    community_aggregates = relationship("CommunityAggregate", back_populates="roll")
    debate_sessions = relationship("DebateSession", back_populates="roll")


class RollPlayer(Base):
    __tablename__ = "roll_players"

    id = Column(Integer, primary_key=True)
    roll_id = Column(Integer, ForeignKey("rolls.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    display_order = Column(Integer, nullable=False)  # Initial random presentation order

    roll = relationship("Roll", back_populates="roll_players")
    player = relationship("Player", back_populates="roll_players")


class Ranking(Base):
    __tablename__ = "rankings"

    id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    roll_id = Column(Integer, ForeignKey("rolls.id"), nullable=False)
    rubric = Column(String(20), nullable=False)  # "analytics" or "reputation"
    player_order = Column(JSON, nullable=False)  # [player_id, player_id, ...]
    kendall_tau_distance = Column(Integer, nullable=False)
    letter_grade = Column(String(1), nullable=False)
    mode = Column(String(20), nullable=False)
    created_at = Column(
        TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        UniqueConstraint("user_id", "roll_id", name="uq_user_daily_ranking"),
    )

    user = relationship("User", back_populates="rankings")
    roll = relationship("Roll", back_populates="rankings")


class CommunityAggregate(Base):
    __tablename__ = "community_aggregates"

    id = Column(Integer, primary_key=True)
    roll_id = Column(Integer, ForeignKey("rolls.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    slot_position = Column(Integer, nullable=False)  # 1-indexed slot
    count = Column(Integer, default=0)
    updated_at = Column(
        TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        UniqueConstraint("roll_id", "player_id", "slot_position", name="uq_community_agg"),
    )

    roll = relationship("Roll", back_populates="community_aggregates")


class DebateSession(Base):
    __tablename__ = "debate_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    roll_id = Column(Integer, ForeignKey("rolls.id"), nullable=False)
    creator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    opponent_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    status = Column(String(20), default="waiting")  # waiting, complete
    created_at = Column(
        TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    roll = relationship("Roll", back_populates="debate_sessions")
    creator = relationship("User", foreign_keys=[creator_id], back_populates="created_debates")


class Friendship(Base):
    __tablename__ = "friendships"

    id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    friend_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(
        TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        UniqueConstraint("user_id", "friend_id", name="uq_friendship"),
        CheckConstraint("user_id != friend_id", name="ck_no_self_friend"),
    )

    user = relationship("User", foreign_keys=[user_id], back_populates="friendships")
