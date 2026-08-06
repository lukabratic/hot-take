"""
Fetch accolades from nba_api for all players in the database.

Pulls All-NBA, All-Star, Championships, and MVP data from
PlayerAwards and PlayerCareerStats endpoints.

Usage:
    python -m pipeline.fetch_accolades
"""

import sys
import time
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import settings
from models import Player


def fetch_player_awards(player_id: int) -> dict:
    """Fetch awards/accolades for a player from nba_api."""
    from nba_api.stats.endpoints import playerawards

    try:
        awards = playerawards.PlayerAwards(player_id=player_id)
        df = awards.get_data_frames()[0]

        if df.empty:
            return {}

        all_nba = 0
        all_star = 0
        champs = 0
        mvp = 0

        for _, row in df.iterrows():
            desc = str(row.get("DESCRIPTION", "")).lower()
            award_type = str(row.get("TYPE", "")).lower()

            if "all-nba" in desc:
                all_nba += 1
            elif "all-star" in desc or "all star" in desc:
                all_star += 1
            elif "champion" in award_type or "nba champion" in desc:
                champs += 1
            elif "mvp" in desc and "all-star" not in desc and "finals" not in desc:
                mvp += 1

        return {
            "all_nba_selections": all_nba,
            "all_star_selections": all_star,
            "championships": champs,
            "mvp_vote_shares": float(mvp),
        }
    except Exception as e:
        print(f"    Warning: Could not fetch awards: {e}")
        return {}


def main():
    db_url = settings.database_url.replace("+asyncpg", "")
    engine = create_engine(db_url)

    with Session(engine) as session:
        players = session.execute(
            select(Player).order_by(Player.name)
        ).scalars().all()

        print(f"Fetching accolades for {len(players)} players from NBA API...")
        print("This will take ~3 minutes due to rate limiting.\n")

        updated = 0
        skipped = 0
        errors = 0

        for i, player in enumerate(players):
            bbref_id = player.bbref_id
            # bbref_id in our DB is the nba_api player_id (numeric string)
            try:
                player_id = int(bbref_id)
            except (ValueError, TypeError):
                print(f"  [{i+1}/{len(players)}] {player.name} - skipping (non-numeric ID)")
                skipped += 1
                continue

            print(f"  [{i+1}/{len(players)}] {player.name}...", end=" ")

            time.sleep(0.7)  # Rate limit

            awards = fetch_player_awards(player_id)

            if awards:
                # Only update if API returned meaningful data
                # (keep our manual data if API returns all zeros for known stars)
                api_total = (
                    awards.get("all_nba_selections", 0)
                    + awards.get("all_star_selections", 0)
                    + awards.get("championships", 0)
                )
                current_total = (
                    player.all_nba_selections
                    + player.all_star_selections
                    + player.championships
                )

                if api_total > current_total:
                    player.all_nba_selections = awards["all_nba_selections"]
                    player.all_star_selections = awards["all_star_selections"]
                    player.championships = awards["championships"]
                    player.mvp_vote_shares = awards["mvp_vote_shares"]
                    print(f"UPDATED ({awards['all_nba_selections']} All-NBA, {awards['all_star_selections']} All-Star, {awards['championships']} Champs)")
                    updated += 1
                else:
                    print(f"kept existing (API: {api_total}, DB: {current_total})")
                    skipped += 1
            else:
                print("no data")
                errors += 1

        session.commit()
        print(f"\nDone! Updated: {updated}, Kept existing: {skipped}, Errors: {errors}")


if __name__ == "__main__":
    main()
