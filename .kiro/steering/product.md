# Product Overview

Hot Take is a daily/on-demand NBA player ranking game. Users rank 5–7 NBA players against a data-driven consensus, scored using Kendall tau distance and assigned a letter grade (S through D). Think Wordle, but for basketball arguments.

## Game Modes

- **Daily Challenge** — One globally shared Roll per day; compare your ranking with the community.
- **Quick Play** — Unlimited random rounds on demand.
- **HoopIQ Mode** — Rank players by stat lines alone (names hidden).
- **Debate Mode** — Challenge a friend to rank the same set head-to-head via a shared link.

## Key Concepts

- **Roll** — A set of 5–7 NBA players presented for ranking, with a position filter and theme modifier.
- **Rubric** — Users choose "Analytics" (advanced stats) or "Reputation" (accolades) before ranking.
- **Kendall Tau Distance** — Measures how far a user's ranking is from the consensus (number of pairwise inversions).
- **Letter Grade** — S (perfect), A (1–2 swaps), B (3–4), C (5–6), D (7+).
- **Reveal Screen** — Shows side-by-side comparison, community heatmap, controversial pick callout, and shareable image card.
- **Streaks** — Track consecutive daily completions.
- **Leaderboards** — Today / Week / All-Time / Friends scopes, backed by Redis sorted sets.

## Authentication

Clerk handles social login and JWT-based auth. Users sync their Clerk identity to a local `users` record.
