# Hot Take NBA Ranking Game

A daily/on-demand web app where players rank 5–7 NBA players against a data-driven consensus. Rankings are scored using Kendall tau distance and assigned a letter grade (S through D). Built to spark debate and shareable moments — think Wordle, but for basketball arguments.

## Features

- **Daily Challenge** — One globally shared Roll per day. Compare your ranking with the community.
- **Quick Play** — Unlimited random rounds on demand.
- **HoopIQ Mode** — Rank players by stat lines alone (names hidden).
- **Debate Mode** — Challenge a friend to rank the same set head-to-head via a shared link.
- **Dual Rubric** — Choose Analytics (advanced stats) or Reputation (accolades) before ranking.
- **Reveal Screen** — Side-by-side comparison, community heatmap, controversial pick callout, and shareable image card.
- **Streaks & Leaderboards** — Track consecutive daily completions and compete on Today/Week/All-Time/Friends scopes.

## Tech Stack

| Layer | Stack |
|-------|-------|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, @dnd-kit, Framer Motion |
| Backend | Python 3.11+, FastAPI, SQLAlchemy (async), Alembic |
| Database | PostgreSQL |
| Cache | Redis |
| Auth | Clerk (social login, JWT) |

## Project Structure

```
hot-take/
├── backend/
│   ├── alembic/          # Database migrations
│   ├── auth/             # Clerk JWT verification, user sync
│   ├── debate/           # Debate mode sessions
│   ├── leaderboard/      # Leaderboard endpoints
│   ├── pipeline/         # Data seeding (Basketball Reference)
│   ├── profile/          # User profile endpoint
│   ├── rankings/         # Ranking submission & scoring
│   ├── rolls/            # Roll generation (daily, quickplay, hoopiq)
│   ├── scoring/          # Kendall tau, consensus, grading
│   ├── streak/           # Daily streak tracking
│   ├── tests/            # pytest test suite
│   ├── main.py           # FastAPI app entry point
│   ├── models.py         # SQLAlchemy models
│   ├── schemas.py        # Pydantic request/response schemas
│   ├── config.py         # Settings (env vars)
│   └── database.py       # Async DB session setup
├── frontend/
│   ├── src/
│   │   ├── components/   # UI components (ranking, reveal, share, etc.)
│   │   ├── hooks/        # Custom React hooks
│   │   ├── pages/        # Route pages (Home, Play, Reveal, etc.)
│   │   ├── services/     # API client with Clerk JWT
│   │   └── types/        # Shared TypeScript interfaces
│   ├── index.html
│   ├── vite.config.ts
│   └── package.json
└── README.md
```

## Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Redis 7+
- A [Clerk](https://clerk.com) account (free tier works)

## Local Setup

### 1. Clone and navigate

```bash
git clone <repo-url>
cd hot-take
```

### 2. Backend

```bash
# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
```

Create `backend/.env`:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/hot_take
REDIS_URL=redis://localhost:6379/0
CLERK_ISSUER=https://<your-clerk-instance>.clerk.accounts.dev
CLERK_JWKS_URL=https://<your-clerk-instance>.clerk.accounts.dev/.well-known/jwks.json
FRONTEND_ORIGIN=http://localhost:5173
```

Set up the database:

```bash
# Create the database
createdb hot_take

# Run migrations
cd backend
alembic upgrade head

# Seed player data
python -m pipeline.seed
```

Start the backend:

```bash
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`. Health check: `GET /health`.

### 3. Frontend

```bash
cd frontend

# Install dependencies
npm install
```

Create `frontend/.env.local`:

```env
VITE_CLERK_PUBLISHABLE_KEY=pk_test_<your-clerk-publishable-key>
```

Start the dev server:

```bash
npm run dev
```

The app will be available at `http://localhost:5173`. The Vite dev server proxies `/api` requests to the backend at port 8000.

## Running Tests

### Backend (pytest)

```bash
cd backend
python -m pytest tests/ -v
```

89 tests covering scoring engine, roll generation, rankings, streaks, and HoopIQ mode.

### Frontend (TypeScript check)

```bash
cd frontend
npx tsc --noEmit
```

### Frontend (production build)

```bash
cd frontend
npm run build
```

## API Overview

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/api/daily` | Today's daily challenge |
| GET | `/api/quickplay` | Random roll |
| GET | `/api/hoopiq` | HoopIQ roll (stats only) |
| POST | `/api/rankings` | Submit a ranking |
| GET | `/api/rankings/:id` | Get ranking result |
| GET | `/api/leaderboard` | Leaderboard (scope query param) |
| POST | `/api/debate` | Create debate session |
| GET | `/api/debate/:id` | Get debate state |
| POST | `/api/debate/:id/ranking` | Submit debate ranking |
| POST | `/api/auth/sync` | Sync Clerk user |
| GET | `/api/profile` | User profile & stats |
| GET | `/api/streak` | Current streak |

## Environment Variables

### Backend

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string (asyncpg) | `postgresql+asyncpg://postgres:postgres@localhost:5432/hot_take` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `CLERK_ISSUER` | Clerk JWT issuer URL | — |
| `CLERK_JWKS_URL` | Clerk JWKS endpoint | — |
| `FRONTEND_ORIGIN` | Allowed CORS origin | `http://localhost:5173` |

### Frontend

| Variable | Description |
|----------|-------------|
| `VITE_CLERK_PUBLISHABLE_KEY` | Clerk publishable key |

## License

Private — not for redistribution.
