"""
Load seed_data.json into the PostgreSQL database.

Usage:
    python -m pipeline.load_db
"""

import json
import math
import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import settings
from models import Base, Player

SEED_DATA_PATH = Path(__file__).parent / "seed_data.json"


def sanitize_stats(stats: dict | None) -> dict | None:
    """Replace NaN/Infinity values with 0.0 so PostgreSQL JSON accepts them."""
    if stats is None:
        return None
    cleaned = {}
    for key, value in stats.items():
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            cleaned[key] = 0.0
        else:
            cleaned[key] = value
    return cleaned


def load_players(session: Session, players: list[dict]) -> None:
    """Insert or update player records in the database."""
    created = 0
    updated = 0

    for player_data in players:
        existing = (
            session.query(Player)
            .filter(Player.bbref_id == player_data["bbref_id"])
            .first()
        )

        if existing:
            # Update existing record
            existing.name = player_data["name"]
            existing.position = player_data["position"]
            existing.era = player_data["era"]
            existing.career_stats = sanitize_stats(player_data["career_stats"])
            existing.peak_stats = sanitize_stats(player_data["peak_stats"])
            existing.playoff_stats = sanitize_stats(player_data["playoff_stats"])
            existing.all_nba_selections = player_data["all_nba_selections"]
            existing.mvp_vote_shares = player_data["mvp_vote_shares"]
            existing.championships = player_data["championships"]
            existing.all_star_selections = player_data["all_star_selections"]
            existing.hof_rank = player_data.get("hof_rank")
            updated += 1
        else:
            # Create new record
            player = Player(
                name=player_data["name"],
                position=player_data["position"],
                era=player_data["era"],
                bbref_id=player_data["bbref_id"],
                career_stats=sanitize_stats(player_data["career_stats"]),
                peak_stats=sanitize_stats(player_data["peak_stats"]),
                playoff_stats=sanitize_stats(player_data["playoff_stats"]),
                all_nba_selections=player_data["all_nba_selections"],
                mvp_vote_shares=player_data["mvp_vote_shares"],
                championships=player_data["championships"],
                all_star_selections=player_data["all_star_selections"],
                hof_rank=player_data.get("hof_rank"),
            )
            session.add(player)
            created += 1

    session.commit()
    print(f"Created {created} new players, updated {updated} existing players.")


def main():
    """Load seed data into the database."""
    if not SEED_DATA_PATH.exists():
        print(f"Error: {SEED_DATA_PATH} not found.")
        print("Run `python -m pipeline.seed` first to generate seed data.")
        sys.exit(1)

    with open(SEED_DATA_PATH) as f:
        # parse_constant handles NaN/Infinity tokens in JSON
        players = json.loads(f.read(), parse_constant=lambda x: 0.0)

    print(f"Loading {len(players)} players into database...")

    # Convert async URL to sync for SQLAlchemy
    db_url = settings.database_url.replace("+asyncpg", "")
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        load_players(session, players)

    print("Done!")


if __name__ == "__main__":
    main()
