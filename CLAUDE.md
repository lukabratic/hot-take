# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Hot Take is a daily/on-demand web app where players rank 5–7 NBA players against a data-driven consensus, scored via Kendall tau distance and a letter grade (S–D). Modes: Daily Challenge, Quick Play, HoopIQ (stats-only, names hidden), and Debate (head-to-head via shared link).

Stack: React 18 + TypeScript + Vite + Tailwind + @dnd-kit + Framer Motion (frontend); Python 3.11+ FastAPI + SQLAlchemy async + Alembic (backend); PostgreSQL; Redis; Clerk for auth.

## Commands

### Backend (run from `backend/`)

```bash
uvicorn main:app --reload --port 8000     # dev server
alembic upgrade head                       # apply migrations
alembic revision -m "description"          # new migration (write upgrade/downgrade by hand — no autogenerate config)
python -m pipeline.seed                    # seed player data
python -m pytest tests/ -v                 # full test suite
python -m pytest tests/test_scoring.py -v  # single file
python -m pytest tests/test_scoring.py::TestKendallTauDistance::test_symmetry -v  # single test
```

There is no `pytest.ini`/`pyproject.toml`; async tests must be marked individually with `@pytest.mark.asyncio` (pytest-asyncio is not in strict/auto mode).

### Frontend (run from `frontend/`)

```bash
npm run dev          # dev server at :5173, proxies /api to :8000
npm run build         # tsc + vite build (this is also the type-check step)
npx tsc --noEmit      # type-check only
```

There is no frontend test runner or lint script configured — `tsc --noEmit` / `npm run build` is the correctness check for frontend changes.

## Architecture

### Backend: router-per-domain module

Each top-level backend package (`auth`, `rolls`, `rankings`, `streak`, `leaderboard`, `debate`, `profile`) owns its own `router.py` mounted in `main.py`, plus its own business logic. There is no separate service layer — routers call directly into sibling modules (e.g. `rolls/router.py` calls `rolls/generator.py`, `rolls/daily.py`, `rolls/quickplay.py`). Follow this pattern for new features: a new domain gets its own package with a `router.py` included in `main.py`.

`scoring/` is the shared, framework-free scoring engine used by both `rankings` and `debate`:
- `kendall_tau.py` — pairwise-inversion distance between two rankings.
- `grading.py` — maps distance → letter grade (S=0, A=1–2, B=3–4, C=5–6, D=7+).
- `consensus.py` — computes the "correct" consensus ranking per rubric/theme.

### Rubrics and themes

Rankings are scored against one of two rubrics — `analytics` (advanced stats) or `reputation` (accolades) — chosen per-round. Rolls also carry a `theme_modifier` (e.g. "Peak Season Only", "Playoff Performance") which changes which stats on `Player` (`career_stats`, `peak_stats`, `playoff_stats`) the consensus is computed from. When touching consensus/grading logic, check `scoring/consensus.py` for how rubric + theme combine before assuming a single code path.

### Data model (`backend/models.py`)

`Roll` (a position + theme_modifier challenge, optionally pinned to a `daily_date`) has many `RollPlayer` (join to `Player`, with `display_order`). A `Ranking` records one user's submitted `player_order` for a `Roll` plus its computed `kendall_tau_distance`/`letter_grade`; `user_id` is nullable to support anonymous submissions (enforced uniqueness only when `user_id IS NOT NULL`, via a partial index added in migration `0003`, not a model-level constraint). `CommunityAggregate` maintains per-slot pick counts per roll for the heatmap. `DebateSession` links two users to a shared `Roll`.

### Auth

Clerk issues the JWT; `auth/middleware.py` verifies it against Clerk's JWKS (cached in-process) and resolves it to a local `User` row keyed by `clerk_id`. Two FastAPI dependencies are used across routers: `get_current_user` (401s if missing/invalid) and `get_optional_user` (returns `None` if no token — used for anonymous-eligible endpoints like ranking submission). If `CLERK_JWKS_URL` is unset, tokens are decoded without signature verification (dev-mode fallback) — don't rely on that path for anything security-sensitive.

### Config

`config.py` reads env vars via `pydantic-settings`. `database_url` is normalized in a validator to always use the `asyncpg` driver, so `DATABASE_URL`/`POSTGRES_URL` can be supplied in any common Postgres URL form (`postgres://`, `postgresql://`, `postgresql+psycopg2://`, etc.) and it gets rewritten to `postgresql+asyncpg://`.

### Pipeline (`backend/pipeline/`)

One-off/offline scripts for building `seed_data.json` from Basketball Reference (`scraper.py`, `fetch_accolades.py`, `fix_accolades.py`, `assign_teams.py`, `generate_seed.py`) and loading it into Postgres (`load_db.py`, `seed.py`). These are run manually, not part of the request/response path.

### Frontend

- `services/api.ts` — single Axios instance; Clerk JWT attached via a request interceptor installed from `hooks/useAuthSync.ts` (not at module init, since Clerk's `getToken` isn't available until the provider mounts).
- `hooks/` — one hook per API resource (`useDaily`, `useRanking`, `useLeaderboard`, `useDebate`, etc.); pages consume hooks rather than calling `services/api.ts` directly.
- `components/` is organized by feature area (`ranking`, `reveal`, `leaderboard`, `debate`, `share`, `category`, `common`), mirroring the backend's domain-package split.
- Drag-and-drop ranking uses `@dnd-kit`; `ArrowRankingBoard`/`BlindRankingBoard`/`RankingBoard` are different presentations of the same ranking interaction (BlindRankingBoard hides names for HoopIQ mode).
