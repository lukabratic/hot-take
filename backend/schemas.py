from pydantic import BaseModel, ConfigDict, Field
from datetime import date, datetime
from typing import Literal
from uuid import UUID


# --- Enums / Literals ---

Position = Literal["PG", "SG", "SF", "PF", "C", "Wings", "Big Men", "Mixed"]
ThemeModifier = Literal[
    "All-Time",
    "Peak Season Only",
    "Playoff Performance",
    "Defensive Impact",
    "Regular Season Only",
    "Championship Era Only",
]
GameMode = Literal["daily", "quickplay", "hoopiq", "debate"]
Rubric = Literal["analytics", "reputation"]
LetterGrade = Literal["S", "A", "B", "C", "D"]


# --- Player Schemas ---


class PlayerStats(BaseModel):
    pts: float = 0.0
    reb: float = 0.0
    ast: float = 0.0
    stl: float = 0.0
    blk: float = 0.0
    per: float = 0.0
    bpm: float = 0.0
    vorp: float = 0.0
    ws: float = 0.0


class PlayerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    position: str
    era: str | None = None
    career_stats: PlayerStats
    peak_stats: PlayerStats
    playoff_stats: PlayerStats | None = None
    all_nba_selections: int = 0
    mvp_vote_shares: float = 0.0
    championships: int = 0
    all_star_selections: int = 0
    hof_rank: int | None = None
    bbref_id: str


class PlayerHoopIQResponse(BaseModel):
    """Player response for HoopIQ mode — no name, photo, or team info."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    career_stats: PlayerStats
    peak_stats: PlayerStats
    playoff_stats: PlayerStats | None = None
    all_nba_selections: int = 0
    all_star_selections: int = 0
    championships: int = 0
    mvp_vote_shares: float = 0.0


# --- Roll Schemas ---


class RollResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    position: Position
    theme_modifier: ThemeModifier
    daily_date: date | None = None
    mode: GameMode
    players: list[PlayerResponse]


class RollHoopIQResponse(BaseModel):
    """Roll response for HoopIQ mode with anonymized players."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    position: Position
    theme_modifier: ThemeModifier
    mode: GameMode
    players: list[PlayerHoopIQResponse]


# --- Ranking Schemas ---


class RankingSubmitRequest(BaseModel):
    roll_id: int
    rubric: Rubric
    player_order: list[int] = Field(..., min_length=5, max_length=7)


class RankingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: UUID | None
    roll_id: int
    rubric: Rubric
    player_order: list[int]
    kendall_tau_distance: int
    letter_grade: LetterGrade
    mode: GameMode
    created_at: datetime


# --- Reveal / Community Schemas ---


class ControversialPickResponse(BaseModel):
    player_id: int
    slot: int
    community_agreement: float


class CommunityHeatmapResponse(BaseModel):
    """Heatmap data: mapping of player_id -> slot -> percentage."""

    data: dict[int, dict[int, float]]
    total_submissions: int


class RevealResponse(BaseModel):
    ranking: RankingResponse
    consensus_order: list[int]
    community_heatmap: CommunityHeatmapResponse
    controversial_pick: ControversialPickResponse | None = None
    commentary: str


# --- Debate Schemas ---


class DebateCreateRequest(BaseModel):
    roll_id: int


class DebateSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    roll_id: int
    creator_id: UUID
    opponent_id: UUID | None = None
    status: str
    created_at: datetime


class DebateRankingSubmitRequest(BaseModel):
    roll_id: int
    rubric: Rubric
    player_order: list[int] = Field(..., min_length=5, max_length=7)


class DebateParticipantResult(BaseModel):
    user_id: UUID
    username: str
    rubric: Rubric
    player_order: list[int]
    kendall_tau_distance: int
    letter_grade: LetterGrade


class DebateCompareResponse(BaseModel):
    session_id: UUID
    status: str
    roll_position: str
    roll_theme_modifier: str
    creator: DebateParticipantResult
    opponent: DebateParticipantResult
    differences: list[int]
    player_names: dict[int, str]


# --- Leaderboard Schemas ---


class LeaderboardEntry(BaseModel):
    rank: int
    user_id: UUID
    username: str
    score: float
    current_streak: int


class LeaderboardResponse(BaseModel):
    scope: str
    entries: list[LeaderboardEntry]


class CategoryLeaderboardEntry(BaseModel):
    rank: int
    user_id: UUID
    username: str
    score: float
    date: str


class CategoryLeaderboardResponse(BaseModel):
    category_value: str
    scope: str
    entries: list[CategoryLeaderboardEntry]


class CategoryBestEntry(BaseModel):
    category_value: str
    best_score: float


class CategoryBestsResponse(BaseModel):
    entries: list[CategoryBestEntry]


# --- Auth / User Schemas ---


class UserSyncRequest(BaseModel):
    clerk_id: str
    username: str
    email: str | None = None
    avatar_url: str | None = None


class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    email: str | None = None
    avatar_url: str | None = None
    current_streak: int
    longest_streak: int
    last_daily_completed: date | None = None
    created_at: datetime


class StreakResponse(BaseModel):
    current_streak: int
    longest_streak: int


# --- Profile Schemas ---


class ProfileRankingHistoryEntry(BaseModel):
    """A single entry in the user's ranking history."""

    id: int
    roll_position: str
    roll_theme_modifier: str
    letter_grade: str
    mode: str
    rubric: str
    kendall_tau_distance: int
    created_at: datetime


class ProfileStatsResponse(BaseModel):
    """Full user profile with aggregated stats and ranking history."""

    id: UUID
    username: str
    avatar_url: str | None = None
    total_games: int
    average_grade: float
    best_grade: str
    current_streak: int
    longest_streak: int
    grade_distribution: dict[str, int]
    recent_history: list[ProfileRankingHistoryEntry]
