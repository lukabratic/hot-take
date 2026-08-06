"""
Basketball Reference scraper for the Hot Take NBA Ranking Game.

Scrapes player career stats, peak season stats, playoff stats, and accolades
from Basketball Reference pages and outputs data in the seed_data.json format.

Usage:
    python -m pipeline.scraper                      # Scrape all target players
    python -m pipeline.scraper --player jordami01   # Scrape a single player by bbref_id
    python -m pipeline.scraper --validate           # Validate output matches schema
    python -m pipeline.scraper --output PATH        # Write to custom output path

IMPORTANT: Basketball Reference has rate limits. This scraper adds delays between
requests (3 seconds minimum) to be respectful of their servers. A full scrape of
~150 players will take 10-15 minutes.
"""

import json
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import httpx

BASE_URL = "https://www.basketball-reference.com"
SEED_DATA_PATH = Path(__file__).parent / "seed_data.json"
REQUEST_DELAY_SECONDS = 3.0

# Map of Basketball Reference position abbreviations to our simplified positions
POSITION_MAP = {
    "PG": "PG",
    "SG": "SG",
    "SF": "SF",
    "PF": "PF",
    "C": "C",
    "G": "PG",
    "F": "SF",
    "G-F": "SG",
    "F-G": "SF",
    "F-C": "PF",
    "C-F": "C",
}


@dataclass
class PlayerStats:
    """Container for a player's per-game stats."""

    pts: float = 0.0
    reb: float = 0.0
    ast: float = 0.0
    stl: float = 0.0
    blk: float = 0.0
    per: float = 15.0
    bpm: float = 0.0
    vorp: float = 0.0
    ws: float = 0.0
    season: Optional[str] = None

    def to_dict(self) -> dict:
        d = {
            "pts": self.pts,
            "reb": self.reb,
            "ast": self.ast,
            "stl": self.stl,
            "blk": self.blk,
            "per": self.per,
            "bpm": self.bpm,
            "vorp": self.vorp,
            "ws": self.ws,
        }
        if self.season is not None:
            d["season"] = self.season
        return d


@dataclass
class PlayerRecord:
    """Complete player record matching seed_data.json format."""

    name: str = ""
    position: str = "SF"
    era: str = "2000s"
    bbref_id: str = ""
    career_stats: PlayerStats = field(default_factory=PlayerStats)
    peak_stats: PlayerStats = field(default_factory=PlayerStats)
    playoff_stats: Optional[PlayerStats] = None
    all_nba_selections: int = 0
    mvp_vote_shares: float = 0.0
    championships: int = 0
    all_star_selections: int = 0
    hof_rank: Optional[int] = None

    def to_dict(self) -> dict:
        d = {
            "name": self.name,
            "position": self.position,
            "era": self.era,
            "bbref_id": self.bbref_id,
            "career_stats": self.career_stats.to_dict(),
            "peak_stats": self.peak_stats.to_dict(),
            "playoff_stats": self.playoff_stats.to_dict() if self.playoff_stats else None,
            "all_nba_selections": self.all_nba_selections,
            "mvp_vote_shares": self.mvp_vote_shares,
            "championships": self.championships,
            "all_star_selections": self.all_star_selections,
            "hof_rank": self.hof_rank,
        }
        return d


# Curated list of ~150 all-time great NBA players by Basketball Reference ID.
# Ensures position diversity and coverage across all eras.
TARGET_PLAYERS = [
    # Point Guards
    "curryst01", "stockjo01", "paulch01", "nashst01", "thomais01",
    "westbru01", "kiddja01", "paytoga01", "rosede01", "lillada01",
    "hardati01", "frazewa01", "couMDbo01", "johnsma02", "parketo01",
    "willijo01", "davisba01", "foxde01", "youngtr01", "moMDja01",
    "gilMDsh01", "irvMDky01", "arenagi01", "bibMDmi01", "marMDst01",
    # Shooting Guards
    "jordami01", "bryMDko01", "wadedw01", "haMDja01", "westje01",
    "iversal01", "drexlcl01", "gervige01", "mcgrMDtr01", "cartMDvi01",
    "richMMmi01", "maravpe01", "haveljo01", "engleal01", "thomMDda01",
    "booMDde01", "edwaMDan01", "mitchdo01", "lavMDza01", "browja01",
    "bealMDbr01", "thompkl01", "butMDji01", "ginobma01", "alleMDra01",
    # Small Forwards
    "jamesMDle01", "duranke01", "doncilu01", "birdla01", "erviMDju01",
    "pippesc01", "piercpa01", "wilkins01", "tatMDja01", "anthoca01",
    "haywMDgo01", "bayloel01", "kingbe01", "woolele01", "grantho01",
    "leonaka01", "georgpa01", "barneba01", "inglMDbr01", "wortja01",
    # Power Forwards
    "malonka01", "duncati01", "giannan01", "nowitdi01", "barkch01",
    "garneke01", "petrobo01", "malonmo01", "ewing01", "webMDch01",
    "mchalke01", "hayesel01", "davisan01", "randMDju01", "adebamba01",
    "loveke01", "aldMLa01", "griffbl01", "porzikr01", "siakpa01",
    # Centers
    "olajuha01", "onealsh01", "robinda01", "chambwi01", "russebi01",
    "howardw01", "mournal01", "embiMDjo01", "jokiMDni01", "townMDka01",
    "reemdwi01", "willipa01", "mutomdi01", "bogMMceMD01", "saborar01",
    "mingya01", "goberru01", "valMDjo01", "adaMDst01", "lopMDbr01",
]


def _safe_float(value: str) -> float:
    """Safely parse a float from a table cell value."""
    if not value or value.strip() == "":
        return 0.0
    try:
        return round(float(value.strip()), 1)
    except (ValueError, TypeError):
        return 0.0


def _parse_html_table_rows(html: str, table_id: str) -> list[dict[str, str]]:
    """
    Parse rows from an HTML table identified by its id attribute.

    Returns a list of dicts mapping column header (data-stat attribute) to cell text.
    Basketball Reference uses data-stat attributes on <td> and <th> elements.
    """
    # Find the table by id
    table_pattern = rf'<table[^>]*id="{table_id}"[^>]*>(.*?)</table>'
    table_match = re.search(table_pattern, html, re.DOTALL)
    if not table_match:
        return []

    table_html = table_match.group(1)

    # Find tbody (skip thead rows)
    tbody_match = re.search(r"<tbody>(.*?)</tbody>", table_html, re.DOTALL)
    if not tbody_match:
        return []

    tbody_html = tbody_match.group(1)

    # Parse each row
    rows = []
    row_pattern = re.compile(r"<tr[^>]*>(.*?)</tr>", re.DOTALL)
    cell_pattern = re.compile(
        r'<(?:td|th)[^>]*data-stat="([^"]*)"[^>]*>(.*?)</(?:td|th)>',
        re.DOTALL,
    )

    for row_match in row_pattern.finditer(tbody_html):
        row_html = row_match.group(1)
        # Skip header/separator rows within tbody
        if 'class="thead"' in row_html or 'class="partial_table"' in row_html:
            continue

        row_data = {}
        for cell_match in cell_pattern.finditer(row_html):
            stat_name = cell_match.group(1)
            cell_content = cell_match.group(2)
            # Strip HTML tags from cell content
            text = re.sub(r"<[^>]+>", "", cell_content).strip()
            row_data[stat_name] = text

        if row_data:
            rows.append(row_data)

    return rows


def _extract_career_totals(rows: list[dict[str, str]]) -> Optional[dict[str, str]]:
    """Find the career totals row (typically the last row or one labeled 'Career')."""
    for row in reversed(rows):
        season = row.get("season", "")
        if "Career" in season or "career" in season:
            return row
    # Fallback: last row
    return rows[-1] if rows else None


def _determine_era(rows: list[dict[str, str]]) -> str:
    """Determine a player's era from their season data."""
    seasons = []
    for row in rows:
        season_str = row.get("season", "")
        # Parse season like "2019-20" -> 2019
        match = re.match(r"(\d{4})", season_str)
        if match:
            seasons.append(int(match.group(1)))

    if not seasons:
        return "2000s"

    mid_year = (min(seasons) + max(seasons)) // 2
    if mid_year < 1970:
        return "1960s"
    elif mid_year < 1980:
        return "1970s"
    elif mid_year < 1990:
        return "1980s"
    elif mid_year < 2000:
        return "1990s"
    elif mid_year < 2010:
        return "2000s"
    elif mid_year < 2020:
        return "2010s"
    else:
        return "2020s"


def _find_peak_season(rows: list[dict[str, str]]) -> Optional[dict[str, str]]:
    """
    Find the player's peak season by PER, falling back to points per game.

    Skips career totals and partial-season (TOT) rows.
    """
    candidates = []
    for row in rows:
        season = row.get("season", "")
        team = row.get("team_id", "")
        # Skip career/totals rows and traded-season aggregates
        if "Career" in season or not season or team == "TOT":
            continue
        # Need at least 40 games to qualify
        gp = _safe_float(row.get("g", "0"))
        if gp < 40:
            continue
        candidates.append(row)

    if not candidates:
        return rows[0] if rows else None

    # Sort by PER first (if available), then by PTS
    def score(r):
        per = _safe_float(r.get("per", "0"))
        pts = _safe_float(r.get("pts_per_g", r.get("pts", "0")))
        return (per if per > 0 else 0, pts)

    return max(candidates, key=score)


def fetch_player_page(bbref_id: str, client: httpx.Client) -> str:
    """
    Fetch a player's Basketball Reference page HTML.

    The URL format is: /players/{first_letter}/{bbref_id}.html
    """
    first_letter = bbref_id[0]
    url = f"{BASE_URL}/players/{first_letter}/{bbref_id}.html"

    response = client.get(url)
    response.raise_for_status()
    return response.text


def parse_player_name(html: str) -> str:
    """Extract the player's name from the page heading."""
    # The name is in an h1 span
    match = re.search(r"<h1[^>]*><span[^>]*>(.*?)</span>", html)
    if match:
        return re.sub(r"<[^>]+>", "", match.group(1)).strip()
    return ""


def parse_player_position(html: str) -> str:
    """Extract the player's primary position from the meta info."""
    # Position is often in the player info section
    match = re.search(r"Position:\s*</strong>\s*(\w[\w\-]*)", html)
    if match:
        pos_str = match.group(1).strip()
        return POSITION_MAP.get(pos_str, POSITION_MAP.get(pos_str.split("-")[0], "SF"))
    return "SF"


def parse_per_game_stats(html: str) -> list[dict[str, str]]:
    """Parse the per_game stats table (regular season per-game averages)."""
    return _parse_html_table_rows(html, "per_game")


def parse_playoff_per_game_stats(html: str) -> list[dict[str, str]]:
    """Parse the playoffs_per_game stats table."""
    return _parse_html_table_rows(html, "playoffs_per_game")


def parse_advanced_stats(html: str) -> list[dict[str, str]]:
    """Parse the advanced stats table (PER, BPM, VORP, WS)."""
    return _parse_html_table_rows(html, "advanced")


def parse_accolades(html: str) -> dict:
    """
    Parse accolades from the player page.

    Looks for All-NBA, MVP, Championships, All-Star selections, and HOF status.
    """
    accolades = {
        "all_nba_selections": 0,
        "mvp_vote_shares": 0.0,
        "championships": 0,
        "all_star_selections": 0,
        "hof_rank": None,
    }

    # All-NBA selections: look for "All-NBA" mentions in the awards section
    all_nba_matches = re.findall(r"All-NBA", html)
    accolades["all_nba_selections"] = len(all_nba_matches) // 2  # rough heuristic (appears in link + text)
    # More precise: count distinct seasons listed under All-NBA
    all_nba_count = len(re.findall(r"<li>\s*\d+x All-NBA", html))
    if all_nba_count > 0:
        accolades["all_nba_selections"] = all_nba_count
    else:
        # Try: "All-NBA First Team" or "All-NBA Second Team" etc.
        team_mentions = re.findall(
            r"All-NBA (?:First|Second|Third) Team", html
        )
        if team_mentions:
            accolades["all_nba_selections"] = len(set(team_mentions))

    # Also try the bling section which lists counts
    bling_match = re.search(
        r'<li[^>]*>\s*<a[^>]*>(\d+)x All-NBA</a>', html
    )
    if bling_match:
        accolades["all_nba_selections"] = int(bling_match.group(1))

    # MVP awards
    mvp_match = re.search(r'(\d+)x\s*(?:NBA )?MVP\b', html)
    if mvp_match:
        accolades["mvp_vote_shares"] = float(mvp_match.group(1))
    elif re.search(r"NBA Most Valuable Player", html):
        # Single MVP
        accolades["mvp_vote_shares"] = 1.0

    # Championships - look for "NBA Champ" in the bling/awards
    champ_match = re.search(r'(\d+)x\s*NBA Champ', html)
    if champ_match:
        accolades["championships"] = int(champ_match.group(1))
    elif re.search(r"NBA Champion\b", html):
        # Count individual championship listings
        champ_count = len(re.findall(r"NBA Champion", html))
        accolades["championships"] = max(1, champ_count // 2)

    # All-Star selections
    allstar_match = re.search(r'(\d+)x\s*All-Star\b', html)
    if allstar_match:
        accolades["all_star_selections"] = int(allstar_match.group(1))
    else:
        allstar_mentions = re.findall(r"NBA All-Star", html)
        accolades["all_star_selections"] = len(allstar_mentions) // 2

    # Hall of Fame
    if re.search(r"Hall of Fame", html, re.IGNORECASE):
        accolades["hof_rank"] = 1  # We don't have actual rank, mark as inducted

    return accolades


def build_career_stats(
    per_game_rows: list[dict[str, str]],
    advanced_rows: list[dict[str, str]],
) -> PlayerStats:
    """Build career stats from the career totals row."""
    career_pg = _extract_career_totals(per_game_rows)
    career_adv = _extract_career_totals(advanced_rows)

    stats = PlayerStats()
    if career_pg:
        stats.pts = _safe_float(career_pg.get("pts_per_g", career_pg.get("pts", "0")))
        stats.reb = _safe_float(career_pg.get("trb_per_g", career_pg.get("trb", "0")))
        stats.ast = _safe_float(career_pg.get("ast_per_g", career_pg.get("ast", "0")))
        stats.stl = _safe_float(career_pg.get("stl_per_g", career_pg.get("stl", "0")))
        stats.blk = _safe_float(career_pg.get("blk_per_g", career_pg.get("blk", "0")))

    if career_adv:
        stats.per = _safe_float(career_adv.get("per", "15"))
        stats.bpm = _safe_float(career_adv.get("bpm", "0"))
        stats.vorp = _safe_float(career_adv.get("vorp", "0"))
        stats.ws = _safe_float(career_adv.get("ws", "0"))

    return stats


def build_peak_stats(
    per_game_rows: list[dict[str, str]],
    advanced_rows: list[dict[str, str]],
) -> PlayerStats:
    """Build peak season stats from the best single season."""
    peak_pg = _find_peak_season(per_game_rows)
    if not peak_pg:
        return PlayerStats()

    season_id = peak_pg.get("season", "")

    # Find the matching advanced stats row for the same season
    peak_adv = None
    for row in advanced_rows:
        if row.get("season", "") == season_id:
            team = row.get("team_id", "")
            if team != "TOT":
                peak_adv = row
                break
    # If no exact match, try first match
    if peak_adv is None:
        for row in advanced_rows:
            if row.get("season", "") == season_id:
                peak_adv = row
                break

    stats = PlayerStats(season=season_id)
    stats.pts = _safe_float(peak_pg.get("pts_per_g", peak_pg.get("pts", "0")))
    stats.reb = _safe_float(peak_pg.get("trb_per_g", peak_pg.get("trb", "0")))
    stats.ast = _safe_float(peak_pg.get("ast_per_g", peak_pg.get("ast", "0")))
    stats.stl = _safe_float(peak_pg.get("stl_per_g", peak_pg.get("stl", "0")))
    stats.blk = _safe_float(peak_pg.get("blk_per_g", peak_pg.get("blk", "0")))

    if peak_adv:
        stats.per = _safe_float(peak_adv.get("per", "15"))
        stats.bpm = _safe_float(peak_adv.get("bpm", "0"))
        stats.vorp = _safe_float(peak_adv.get("vorp", "0"))
        stats.ws = _safe_float(peak_adv.get("ws", "0"))

    return stats


def build_playoff_stats(
    playoff_rows: list[dict[str, str]],
    advanced_rows: list[dict[str, str]],
) -> Optional[PlayerStats]:
    """Build career playoff stats from the playoff totals."""
    if not playoff_rows:
        return None

    career_row = _extract_career_totals(playoff_rows)
    if not career_row:
        return None

    stats = PlayerStats()
    stats.pts = _safe_float(career_row.get("pts_per_g", career_row.get("pts", "0")))
    stats.reb = _safe_float(career_row.get("trb_per_g", career_row.get("trb", "0")))
    stats.ast = _safe_float(career_row.get("ast_per_g", career_row.get("ast", "0")))
    stats.stl = _safe_float(career_row.get("stl_per_g", career_row.get("stl", "0")))
    stats.blk = _safe_float(career_row.get("blk_per_g", career_row.get("blk", "0")))

    # Playoff advanced stats are harder to get from a separate table.
    # Use per-game PER approximation if advanced playoff table not available.
    # Basketball Reference has a playoffs_advanced table on some pages.
    playoff_adv_rows = []
    for row in advanced_rows:
        # The advanced table includes regular season only on the main page.
        # We'll approximate PER from box score for playoffs.
        pass

    # Approximate advanced metrics from playoff per-game stats
    if stats.pts > 0:
        # Simplified PER approximation for playoffs
        stats.per = round(
            max(
                5.0,
                min(
                    35.0,
                    (stats.pts + stats.reb * 1.2 + stats.ast * 1.5
                     + stats.stl * 2.0 + stats.blk * 2.0) * 0.55 + 2.0,
                ),
            ),
            1,
        )
        stats.bpm = round(
            (stats.pts - 15.0) * 0.12
            + (stats.reb - 5.0) * 0.1
            + (stats.ast - 3.0) * 0.15
            + (stats.stl - 0.8) * 1.2
            + (stats.blk - 0.5) * 1.0,
            1,
        )
        stats.bpm = max(-10.0, min(15.0, stats.bpm))

    return stats


def scrape_player(bbref_id: str, client: httpx.Client) -> Optional[PlayerRecord]:
    """
    Scrape a single player's data from Basketball Reference.

    Returns a PlayerRecord or None if the page couldn't be parsed.
    """
    try:
        html = fetch_player_page(bbref_id, client)
    except httpx.HTTPStatusError as e:
        print(f"  HTTP error fetching {bbref_id}: {e.response.status_code}")
        return None
    except httpx.RequestError as e:
        print(f"  Request error fetching {bbref_id}: {e}")
        return None

    name = parse_player_name(html)
    if not name:
        print(f"  Could not parse name for {bbref_id}")
        return None

    position = parse_player_position(html)
    per_game_rows = parse_per_game_stats(html)
    playoff_rows = parse_playoff_per_game_stats(html)
    advanced_rows = parse_advanced_stats(html)

    if not per_game_rows:
        print(f"  No per-game stats found for {name} ({bbref_id})")
        return None

    era = _determine_era(per_game_rows)
    career_stats = build_career_stats(per_game_rows, advanced_rows)
    peak_stats = build_peak_stats(per_game_rows, advanced_rows)
    playoff_stats = build_playoff_stats(playoff_rows, advanced_rows)
    accolades = parse_accolades(html)

    record = PlayerRecord(
        name=name,
        position=position,
        era=era,
        bbref_id=bbref_id,
        career_stats=career_stats,
        peak_stats=peak_stats,
        playoff_stats=playoff_stats,
        all_nba_selections=accolades["all_nba_selections"],
        mvp_vote_shares=accolades["mvp_vote_shares"],
        championships=accolades["championships"],
        all_star_selections=accolades["all_star_selections"],
        hof_rank=accolades["hof_rank"],
    )
    return record



def validate_player_record(player: dict) -> list[str]:
    """Validate a player record matches the seed_data.json schema."""
    errors = []

    # Required string fields
    for field_name in ["name", "position", "era", "bbref_id"]:
        if not isinstance(player.get(field_name), str) or not player[field_name]:
            errors.append(f"Missing or invalid string field: {field_name}")

    if player.get("position") not in ("PG", "SG", "SF", "PF", "C"):
        errors.append(f"Invalid position: {player.get('position')}")

    # Career stats
    career = player.get("career_stats")
    if not isinstance(career, dict):
        errors.append("career_stats must be a dict")
    else:
        for stat in ["pts", "reb", "ast", "stl", "blk", "per", "bpm", "vorp", "ws"]:
            if stat not in career:
                errors.append(f"career_stats missing: {stat}")
            elif not isinstance(career[stat], (int, float)):
                errors.append(f"career_stats.{stat} must be numeric")

    # Peak stats
    peak = player.get("peak_stats")
    if not isinstance(peak, dict):
        errors.append("peak_stats must be a dict")
    else:
        for stat in ["pts", "reb", "ast", "per", "bpm", "vorp", "ws"]:
            if stat not in peak:
                errors.append(f"peak_stats missing: {stat}")

    # Playoff stats (can be None)
    playoff = player.get("playoff_stats")
    if playoff is not None and not isinstance(playoff, dict):
        errors.append("playoff_stats must be a dict or null")

    # Accolades
    for field_name in ["all_nba_selections", "championships", "all_star_selections"]:
        val = player.get(field_name)
        if not isinstance(val, (int, float)) or val < 0:
            errors.append(f"{field_name} must be a non-negative number")

    if not isinstance(player.get("mvp_vote_shares", 0), (int, float)):
        errors.append("mvp_vote_shares must be numeric")

    return errors


def scrape_all_players(
    player_ids: Optional[list[str]] = None,
    delay: float = REQUEST_DELAY_SECONDS,
) -> list[dict]:
    """
    Scrape all target players from Basketball Reference.

    Args:
        player_ids: List of bbref_ids to scrape. Defaults to TARGET_PLAYERS.
        delay: Seconds to wait between requests (be respectful of rate limits).

    Returns:
        List of player record dicts ready for seed_data.json.
    """
    targets = player_ids or TARGET_PLAYERS
    players = []

    headers = {
        "User-Agent": "HotTakeNBA/1.0 (educational project; respectful scraping)",
        "Accept": "text/html,application/xhtml+xml",
    }

    with httpx.Client(
        headers=headers,
        follow_redirects=True,
        timeout=30.0,
    ) as client:
        total = len(targets)
        for idx, bbref_id in enumerate(targets):
            print(f"  [{idx + 1}/{total}] Scraping {bbref_id}...")

            record = scrape_player(bbref_id, client)
            if record:
                player_dict = record.to_dict()
                errors = validate_player_record(player_dict)
                if errors:
                    print(f"    Validation warnings for {record.name}: {errors}")
                players.append(player_dict)
                print(f"    OK: {record.name} ({record.position}, {record.era})")
            else:
                print(f"    SKIP: Could not scrape {bbref_id}")

            # Rate limit - be respectful
            if idx < total - 1:
                time.sleep(delay)

    return players


def save_seed_data(players: list[dict], output_path: Optional[Path] = None) -> None:
    """Save scraped player data to JSON file in seed_data format."""
    path = output_path or SEED_DATA_PATH
    with open(path, "w") as f:
        json.dump(players, f, indent=2, ensure_ascii=False)
    print(f"\nSaved {len(players)} players to {path}")


def validate_existing_data(path: Optional[Path] = None) -> bool:
    """Validate an existing seed_data.json file."""
    data_path = path or SEED_DATA_PATH
    if not data_path.exists():
        print(f"File not found: {data_path}")
        return False

    with open(data_path) as f:
        players = json.load(f)

    print(f"Loaded {len(players)} players from {data_path}")

    all_valid = True
    position_counts = {"PG": 0, "SG": 0, "SF": 0, "PF": 0, "C": 0}
    bbref_ids = set()

    for i, player in enumerate(players):
        errors = validate_player_record(player)
        if errors:
            print(f"  Player {i} ({player.get('name', 'unknown')}): {errors}")
            all_valid = False
        else:
            pos = player["position"]
            position_counts[pos] = position_counts.get(pos, 0) + 1

            if player["bbref_id"] in bbref_ids:
                print(f"  Duplicate bbref_id: {player['bbref_id']}")
                all_valid = False
            bbref_ids.add(player["bbref_id"])

    print(f"\n  Position distribution: {position_counts}")
    print(f"  Total valid players: {sum(position_counts.values())}")
    if all_valid:
        print("  All records valid!")
    return all_valid


def main():
    """Main entry point for the Basketball Reference scraper."""
    args = sys.argv[1:]

    if "--validate" in args:
        output_path = None
        if "--output" in args:
            idx = args.index("--output")
            if idx + 1 < len(args):
                output_path = Path(args[idx + 1])
        is_valid = validate_existing_data(output_path)
        sys.exit(0 if is_valid else 1)

    if "--player" in args:
        idx = args.index("--player")
        if idx + 1 >= len(args):
            print("Usage: --player <bbref_id>")
            sys.exit(1)
        player_id = args[idx + 1]
        print(f"Scraping single player: {player_id}")
        players = scrape_all_players(player_ids=[player_id], delay=0)
        if players:
            print(json.dumps(players[0], indent=2, ensure_ascii=False))
        else:
            print("Failed to scrape player.")
            sys.exit(1)
        return

    output_path = None
    if "--output" in args:
        idx = args.index("--output")
        if idx + 1 < len(args):
            output_path = Path(args[idx + 1])

    print("Basketball Reference Scraper for Hot Take NBA Ranking Game")
    print("=" * 60)
    print(f"Target: {len(TARGET_PLAYERS)} players")
    print(f"Delay between requests: {REQUEST_DELAY_SECONDS}s")
    print(f"Estimated time: ~{len(TARGET_PLAYERS) * REQUEST_DELAY_SECONDS / 60:.0f} minutes")
    print("=" * 60)
    print()

    players = scrape_all_players()
    if not players:
        print("No players scraped successfully.")
        sys.exit(1)

    save_seed_data(players, output_path)

    print("\nValidating output...")
    is_valid = validate_existing_data(output_path)
    if not is_valid:
        print("\nWARNING: Some records have validation issues.")
        sys.exit(1)

    print(f"\nDone! {len(players)} players scraped and saved.")


if __name__ == "__main__":
    main()
