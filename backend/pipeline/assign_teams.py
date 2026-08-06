"""
Assign team and conference data to existing players in the database.

Maps each player to their most iconic/primary franchise.

Usage:
    python -m pipeline.assign_teams
"""

import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import settings
from models import Base, Player

# Conference lookup by team
EASTERN_TEAMS = {
    "Celtics", "Nets", "Knicks", "76ers", "Raptors",
    "Bulls", "Cavaliers", "Pistons", "Pacers", "Bucks",
    "Hawks", "Hornets", "Heat", "Magic", "Wizards",
}

WESTERN_TEAMS = {
    "Lakers", "Clippers", "Warriors", "Suns", "Kings",
    "Nuggets", "Timberwolves", "Thunder", "Trail Blazers", "Jazz",
    "Mavericks", "Rockets", "Grizzlies", "Pelicans", "Spurs",
}

# Player -> primary team mapping (most iconic franchise)
PLAYER_TEAMS = {
    "Adrian Dantley": "Jazz",
    "Alex English": "Nuggets",
    "Allen Iverson": "76ers",
    "Alonzo Mourning": "Heat",
    "Amar'e Stoudemire": "Suns",
    "Andrew Wiggins": "Warriors",
    "Antawn Jamison": "Wizards",
    "Anthony Davis": "Lakers",
    "Anthony Edwards": "Timberwolves",
    "Artis Gilmore": "Bulls",
    "Bailey Howell": "Pistons",
    "Bernard King": "Knicks",
    "Billy Cunningham": "76ers",
    "Blake Griffin": "Clippers",
    "Bob Cousy": "Celtics",
    "Bob Dandridge": "Bucks",
    "Bob Lanier": "Pistons",
    "Bob McAdoo": "Lakers",
    "Bob Pettit": "Hawks",
    "Bob Rule": "Kings",
    "Brad Daugherty": "Cavaliers",
    "Bradley Beal": "Wizards",
    "Brandon Ingram": "Pelicans",
    "CJ McCollum": "Trail Blazers",
    "Carmelo Anthony": "Nuggets",
    "Charles Barkley": "76ers",
    "Chet Walker": "Bulls",
    "Chris Bosh": "Heat",
    "Chris Mullin": "Warriors",
    "Chris Webber": "Kings",
    "Cliff Hagan": "Hawks",
    "Clyde Drexler": "Trail Blazers",
    "Collin Sexton": "Cavaliers",
    "Damian Lillard": "Trail Blazers",
    "Dan Issel": "Nuggets",
    "Darius Garland": "Cavaliers",
    "Dave Bing": "Pistons",
    "Dave Cowens": "Celtics",
    "David Robinson": "Spurs",
    "David Thompson": "Nuggets",
    "De'Aaron Fox": "Kings",
    "DeMar DeRozan": "Raptors",
    "DeMarcus Cousins": "Kings",
    "Devin Booker": "Suns",
    "Dirk Nowitzki": "Mavericks",
    "Dolph Schayes": "76ers",
    "Dominique Wilkins": "Hawks",
    "Donovan Mitchell": "Cavaliers",
    "Dwyane Wade": "Heat",
    "Earl Monroe": "Knicks",
    "Ed Macauley": "Celtics",
    "Elgin Baylor": "Lakers",
    "Elvin Hayes": "Rockets",
    "Gail Goodrich": "Lakers",
    "Geoff Petrie": "Trail Blazers",
    "George Gervin": "Spurs",
    "George Mikan": "Lakers",
    "George Yardley": "Pistons",
    "Giannis Antetokounmpo": "Bucks",
    "Gilbert Arenas": "Wizards",
    "Grant Hill": "Pistons",
    "Hakeem Olajuwon": "Rockets",
    "Hal Greer": "76ers",
    "Isaiah Thomas": "Celtics",
    "Isiah Thomas": "Pistons",
    "Jack Sikma": "Kings",
    "Jack Twyman": "Kings",
    "James Harden": "Rockets",
    "James Worthy": "Lakers",
    "Jason Kidd": "Nets",
    "Jayson Tatum": "Celtics",
    "Jerry West": "Lakers",
    "Jimmy Butler": "Heat",
    "Joel Embiid": "76ers",
    "John Drew": "Hawks",
    "John Havlicek": "Celtics",
    "John Stockton": "Jazz",
    "Julius Erving": "76ers",
    "Karl Malone": "Jazz",
    "Karl-Anthony Towns": "Timberwolves",
    "Kareem Abdul-Jabbar": "Lakers",
    "Kevin Durant": "Thunder",
    "Kevin Garnett": "Timberwolves",
    "Kevin Love": "Cavaliers",
    "Kevin McHale": "Celtics",
    "Kobe Bryant": "Lakers",
    "Kyrie Irving": "Cavaliers",
    "LaMarcus Aldridge": "Trail Blazers",
    "Larry Bird": "Celtics",
    "LeBron James": "Lakers",
    "Luka Doncic": "Mavericks",
    "Magic Johnson": "Lakers",
    "Manu Ginobili": "Spurs",
    "Mark Aguirre": "Mavericks",
    "Michael Jordan": "Bulls",
    "Mike Mitchell": "Spurs",
    "Mitch Richmond": "Kings",
    "Moses Malone": "Rockets",
    "Nate Archibald": "Kings",
    "Nikola Jokic": "Nuggets",
    "Oscar Robertson": "Bucks",
    "Patrick Ewing": "Knicks",
    "Paul Arizin": "Warriors",
    "Paul George": "Pacers",
    "Paul Pierce": "Celtics",
    "Pau Gasol": "Lakers",
    "Pete Maravich": "Jazz",
    "Ray Allen": "Celtics",
    "Reggie Miller": "Pacers",
    "Rick Barry": "Warriors",
    "Robert Parish": "Celtics",
    "Russell Westbrook": "Thunder",
    "Sam Jones": "Celtics",
    "Scottie Pippen": "Bulls",
    "Shaquille O'Neal": "Lakers",
    "Shai Gilgeous-Alexander": "Thunder",
    "Stephen Curry": "Warriors",
    "Steve Nash": "Suns",
    "Terry Cummings": "Bucks",
    "Tim Duncan": "Spurs",
    "Tim Hardaway": "Warriors",
    "Tom Chambers": "Suns",
    "Tony Parker": "Spurs",
    "Tracy McGrady": "Magic",
    "Trae Young": "Hawks",
    "Vince Carter": "Raptors",
    "Walt Bellamy": "Bulls",
    "Walt Frazier": "Knicks",
    "Wilt Chamberlain": "Warriors",
    "World B. Free": "76ers",
    "Zach LaVine": "Bulls",
    "Zach Randolph": "Grizzlies",
    # Round 2 additions
    "Glen Rice": "Heat",
    "Glenn Robinson": "Bucks",
    "Jalen Brunson": "Knicks",
    "Jamal Mashburn": "Mavericks",
    "Jamal Murray": "Nuggets",
    "Jaren Jackson Jr.": "Grizzlies",
    "Jaylen Brown": "Celtics",
    "Jeff Malone": "Wizards",
    "Jimmy Butler III": "Heat",
    "Joe Barry Carroll": "Warriors",
    "John Wall": "Wizards",
    "Julius Randle": "Knicks",
    "Kawhi Leonard": "Spurs",
    "Kemba Walker": "Hornets",
    "Kiki Vandeweghe": "Nuggets",
    "Klay Thompson": "Warriors",
    "Kristaps Porziņģis": "Mavericks",
    "Latrell Sprewell": "Knicks",
    "Lauri Markkanen": "Jazz",
    "Lou Hudson": "Hawks",
    "Luka Dončić": "Mavericks",
    "Marques Johnson": "Bucks",
    "Michael Redd": "Bucks",
    "Neil Johnston": "Warriors",
    "Nikola Jokić": "Nuggets",
    "Nikola Vučević": "Magic",
    "Otis Birdsong": "Nets",
    "Pascal Siakam": "Raptors",
    "RJ Barrett": "Knicks",
    "Reggie Theus": "Kings",
    "Rolando Blackman": "Mavericks",
    "Shareef Abdur-Rahim": "Grizzlies",
    "Spencer Haywood": "Knicks",
    "Stephon Marbury": "Knicks",
    "Steve Francis": "Rockets",
    "Tom Heinsohn": "Celtics",
    "Walter Davis": "Suns",
    "Willis Reed": "Knicks",
    "World Free": "76ers",
    "Yao Ming": "Rockets",
}


def get_conference(team: str) -> str | None:
    if team in EASTERN_TEAMS:
        return "Eastern"
    elif team in WESTERN_TEAMS:
        return "Western"
    return None


def main():
    db_url = settings.database_url.replace("+asyncpg", "")
    engine = create_engine(db_url)

    with Session(engine) as session:
        players = session.query(Player).all()
        updated = 0
        missing = []

        for player in players:
            team = PLAYER_TEAMS.get(player.name)
            if team:
                player.team = team
                player.conference = get_conference(team)
                updated += 1
            else:
                missing.append(player.name)

        session.commit()
        print(f"Updated {updated} players with team/conference data.")

        if missing:
            print(f"\n{len(missing)} players without team mapping:")
            for name in sorted(missing):
                print(f"  - {name}")
            print("\nAdd these to PLAYER_TEAMS in assign_teams.py and re-run.")


if __name__ == "__main__":
    main()
