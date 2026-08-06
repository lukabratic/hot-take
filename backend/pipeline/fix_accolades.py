"""
Fix accolades for all 150 players in the database.

Usage:
    python -m pipeline.fix_accolades
"""

import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import settings
from models import Player

# Format: "Player Name": (all_nba, all_star, championships, mvp_vote_shares, hof_rank)
# hof_rank = None means not in HOF (or not yet eligible)
ACCOLADES = {
    "Adrian Dantley": (2, 6, 0, 0.0, 25),
    "Alex English": (3, 8, 0, 0.0, 26),
    "Allen Iverson": (7, 11, 0, 1.0, 24),
    "Alonzo Mourning": (2, 7, 1, 0.0, 27),
    "Amar'e Stoudemire": (5, 6, 0, 0.0, None),
    "Andrew Wiggins": (0, 1, 1, 0.0, None),
    "Antawn Jamison": (0, 2, 0, 0.0, None),
    "Anthony Davis": (4, 9, 1, 0.0, None),
    "Anthony Edwards": (1, 3, 0, 0.0, None),
    "Artis Gilmore": (0, 6, 0, 0.0, 28),
    "Bailey Howell": (0, 6, 2, 0.0, None),
    "Bernard King": (2, 4, 0, 0.0, 29),
    "Billy Cunningham": (3, 4, 1, 0.0, 30),
    "Blake Griffin": (3, 6, 0, 0.0, None),
    "Bob Cousy": (10, 13, 6, 1.0, 5),
    "Bob Dandridge": (0, 4, 2, 0.0, None),
    "Bob Lanier": (1, 8, 0, 0.0, 31),
    "Bob McAdoo": (2, 5, 2, 1.0, 32),
    "Bob Pettit": (10, 11, 1, 2.0, 3),
    "Bob Rule": (0, 2, 0, 0.0, None),
    "Brad Daugherty": (0, 5, 0, 0.0, None),
    "Bradley Beal": (0, 3, 1, 0.0, None),
    "Brandon Ingram": (0, 1, 0, 0.0, None),
    "Carmelo Anthony": (6, 10, 0, 0.0, None),
    "Charles Barkley": (11, 11, 0, 1.0, 10),
    "Chet Walker": (0, 7, 1, 0.0, None),
    "Chris Bosh": (1, 11, 2, 0.0, 33),
    "Chris Mullin": (3, 5, 0, 0.0, 34),
    "Chris Webber": (3, 5, 0, 0.0, None),
    "CJ McCollum": (0, 1, 0, 0.0, None),
    "Cliff Hagan": (0, 5, 1, 0.0, 35),
    "Clyde Drexler": (3, 10, 1, 0.0, 12),
    "Collin Sexton": (0, 0, 0, 0.0, None),
    "Damian Lillard": (6, 7, 0, 0.0, None),
    "Dan Issel": (0, 6, 0, 0.0, 36),
    "Darius Garland": (0, 1, 0, 0.0, None),
    "Dave Bing": (2, 7, 0, 0.0, 37),
    "Dave Cowens": (3, 7, 2, 1.0, 38),
    "David Robinson": (10, 10, 2, 1.0, 8),
    "David Thompson": (2, 4, 0, 0.0, 39),
    "De'Aaron Fox": (1, 1, 0, 0.0, None),
    "DeMar DeRozan": (3, 6, 0, 0.0, None),
    "DeMarcus Cousins": (2, 4, 0, 0.0, None),
    "Devin Booker": (2, 4, 0, 0.0, None),
    "Dirk Nowitzki": (12, 14, 1, 1.0, 14),
    "Dolph Schayes": (6, 12, 1, 0.0, 4),
    "Dominique Wilkins": (3, 9, 0, 0.0, 40),
    "Donovan Mitchell": (1, 3, 0, 0.0, None),
    "Dwyane Wade": (8, 13, 3, 0.0, 11),
    "Earl Monroe": (0, 4, 1, 0.0, 41),
    "Ed Macauley": (3, 7, 1, 0.0, 42),
    "Elgin Baylor": (10, 11, 0, 0.0, 6),
    "Elvin Hayes": (3, 12, 1, 0.0, 43),
    "Gail Goodrich": (1, 5, 1, 0.0, 44),
    "Geoff Petrie": (0, 2, 0, 0.0, None),
    "George Gervin": (5, 9, 0, 0.0, 13),
    "George Mikan": (6, 4, 5, 0.0, 1),
    "George Yardley": (1, 6, 0, 0.0, 45),
    "Giannis Antetokounmpo": (7, 8, 1, 2.0, None),
    "Gilbert Arenas": (1, 3, 0, 0.0, None),
    "Glen Rice": (1, 3, 1, 0.0, None),
    "Glenn Robinson": (0, 2, 0, 0.0, None),
    "Hakeem Olajuwon": (12, 12, 2, 1.0, 7),
    "Hal Greer": (7, 10, 1, 0.0, 46),
    "Isiah Thomas": (5, 12, 2, 0.0, 15),
    "Jack Twyman": (2, 6, 0, 0.0, 47),
    "Jalen Brunson": (1, 1, 0, 0.0, None),
    "Jamal Mashburn": (0, 1, 0, 0.0, None),
    "Jamal Murray": (0, 1, 0, 0.0, None),
    "James Harden": (7, 10, 0, 1.0, None),
    "Jaren Jackson Jr.": (1, 1, 0, 0.0, None),
    "Jaylen Brown": (1, 3, 1, 0.0, None),
    "Jayson Tatum": (4, 5, 1, 0.0, None),
    "Jeff Malone": (0, 2, 0, 0.0, None),
    "Jerry West": (12, 14, 1, 0.0, 2),
    "Jimmy Butler III": (4, 6, 0, 0.0, None),
    "Joe Barry Carroll": (0, 1, 0, 0.0, None),
    "Joel Embiid": (5, 7, 0, 1.0, None),
    "John Drew": (0, 2, 0, 0.0, None),
    "John Havlicek": (11, 13, 8, 0.0, 9),
    "John Wall": (1, 5, 0, 0.0, None),
    "Julius Erving": (11, 11, 1, 1.0, 16),
    "Julius Randle": (1, 1, 0, 0.0, None),
    "Kareem Abdul-Jabbar": (15, 19, 6, 6.0, 2),
    "Karl Malone": (14, 14, 0, 2.0, 17),
    "Karl-Anthony Towns": (0, 4, 0, 0.0, None),
    "Kawhi Leonard": (4, 5, 2, 0.0, None),
    "Kemba Walker": (0, 4, 0, 0.0, None),
    "Kevin Durant": (10, 14, 2, 1.0, None),
    "Kiki Vandeweghe": (0, 2, 0, 0.0, None),
    "Klay Thompson": (2, 5, 4, 0.0, None),
    "Kobe Bryant": (15, 18, 5, 1.0, 18),
    "Kristaps Porziņģis": (0, 2, 1, 0.0, None),
    "Kyrie Irving": (3, 8, 1, 0.0, None),
    "LaMarcus Aldridge": (5, 7, 0, 0.0, None),
    "Larry Bird": (10, 12, 3, 3.0, 19),
    "Latrell Sprewell": (0, 4, 0, 0.0, None),
    "Lauri Markkanen": (0, 1, 0, 0.0, None),
    "LeBron James": (19, 20, 4, 4.0, None),
    "Lou Hudson": (0, 6, 0, 0.0, None),
    "Luka Dončić": (5, 5, 0, 0.0, None),
    "Magic Johnson": (10, 12, 5, 3.0, 20),
    "Mark Aguirre": (0, 3, 2, 0.0, None),
    "Marques Johnson": (1, 3, 0, 0.0, None),
    "Michael Jordan": (11, 14, 6, 5.0, 1),
    "Michael Redd": (0, 1, 0, 0.0, None),
    "Mike Mitchell": (0, 2, 0, 0.0, None),
    "Mitch Richmond": (3, 6, 0, 0.0, 48),
    "Moses Malone": (8, 12, 1, 3.0, 21),
    "Nate Archibald": (3, 6, 1, 0.0, 49),
    "Neil Johnston": (4, 6, 0, 0.0, 50),
    "Nikola Jokić": (7, 6, 1, 3.0, None),
    "Nikola Vučević": (0, 2, 0, 0.0, None),
    "Oscar Robertson": (11, 12, 1, 1.0, 22),
    "Otis Birdsong": (0, 4, 0, 0.0, None),
    "Pascal Siakam": (1, 2, 1, 0.0, None),
    "Patrick Ewing": (7, 11, 0, 0.0, 23),
    "Pau Gasol": (4, 6, 2, 0.0, None),
    "Paul Arizin": (3, 10, 1, 0.0, 51),
    "Paul George": (6, 7, 0, 0.0, None),
    "Paul Pierce": (4, 10, 1, 0.0, None),
    "Pete Maravich": (2, 5, 0, 0.0, 52),
    "Ray Allen": (2, 10, 2, 0.0, 53),
    "Reggie Miller": (3, 5, 0, 0.0, 54),
    "Reggie Theus": (0, 2, 0, 0.0, None),
    "Rick Barry": (5, 8, 1, 0.0, 55),
    "RJ Barrett": (0, 0, 0, 0.0, None),
    "Rolando Blackman": (0, 4, 0, 0.0, None),
    "Russell Westbrook": (9, 9, 0, 1.0, None),
    "Shai Gilgeous-Alexander": (3, 3, 0, 0.0, None),
    "Shaquille O'Neal": (14, 15, 4, 1.0, 56),
    "Shareef Abdur-Rahim": (0, 1, 0, 0.0, None),
    "Spencer Haywood": (2, 4, 0, 0.0, 57),
    "Stephen Curry": (10, 10, 4, 2.0, None),
    "Stephon Marbury": (0, 2, 0, 0.0, None),
    "Steve Francis": (0, 3, 0, 0.0, None),
    "Tim Duncan": (15, 15, 5, 2.0, 58),
    "Tom Chambers": (0, 4, 0, 0.0, None),
    "Tom Heinsohn": (0, 6, 8, 0.0, 59),
    "Tracy McGrady": (5, 7, 0, 0.0, 60),
    "Trae Young": (0, 3, 0, 0.0, None),
    "Vince Carter": (0, 8, 0, 0.0, None),
    "Walt Bellamy": (1, 4, 0, 0.0, 61),
    "Walt Frazier": (4, 7, 2, 0.0, 62),
    "Walter Davis": (0, 6, 0, 0.0, None),
    "Willis Reed": (5, 7, 2, 1.0, 63),
    "Wilt Chamberlain": (10, 13, 2, 4.0, 64),
    "World Free": (0, 1, 0, 0.0, None),
    "Yao Ming": (2, 8, 0, 0.0, 65),
    "Zach LaVine": (0, 2, 0, 0.0, None),
}


def main():
    db_url = settings.database_url.replace("+asyncpg", "")
    engine = create_engine(db_url)

    with Session(engine) as session:
        players = session.query(Player).all()
        updated = 0
        missing = []

        for player in players:
            accolades = ACCOLADES.get(player.name)
            if accolades:
                all_nba, all_star, champs, mvp, hof = accolades
                player.all_nba_selections = all_nba
                player.all_star_selections = all_star
                player.championships = champs
                player.mvp_vote_shares = mvp
                player.hof_rank = hof
                updated += 1
            else:
                missing.append(player.name)

        session.commit()
        print(f"Updated accolades for {updated} players.")

        if missing:
            print(f"\n{len(missing)} players without accolade mapping:")
            for name in sorted(missing):
                print(f"  - {name}")


if __name__ == "__main__":
    main()
