# Project Structure

## Layout

```
hot-take/
├── backend/           # Python FastAPI application
│   ├── main.py        # App entry point, router registration, CORS
│   ├── config.py      # Settings from env vars (pydantic-settings)
│   ├── database.py    # Async SQLAlchemy engine & session factory
│   ├── models.py      # All SQLAlchemy ORM models
│   ├── schemas.py     # All Pydantic request/response schemas
│   ├── alembic/       # Database migrations
│   ├── auth/          # Clerk JWT verification, user sync endpoint
│   ├── rolls/         # Roll generation (daily, quickplay, hoopiq, categories)
│   ├── rankings/      # Ranking submission & scoring integration
│   ├── scoring/       # Kendall tau, consensus algorithms, grading
│   ├── streak/        # Daily streak tracking logic
│   ├── leaderboard/   # Leaderboard endpoints (Redis sorted sets)
│   ├── debate/        # Debate mode session management
│   ├── profile/       # User profile & stats endpoint
│   ├── pipeline/      # Data seeding from Basketball Reference / NBA API
│   └── tests/         # pytest test suite
├── frontend/          # React + TypeScript + Vite SPA
│   ├── src/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── pages/
│   │   ├── services/
│   │   └── types/
│   └── index.html
└── README.md
```

## Architecture Patterns

### Backend

- **Domain modules**: Each feature is a self-contained package (`auth/`, `rolls/`, `scoring/`, etc.) with its own `router.py` and supporting logic files.
- **Single models file**: All SQLAlchemy models live in `backend/models.py`.
- **Single schemas file**: All Pydantic schemas live in `backend/schemas.py`.
- **Dependency injection**: FastAPI `Depends()` for DB sessions, Redis clients, and auth.
- **Async throughout**: All DB access and external calls use async/await.
- **Router prefixes**: All API routes use `/api` prefix (e.g., `/api/daily`, `/api/rankings`).

### Auth Flow

1. Frontend authenticates via Clerk SDK.
2. JWT sent in `Authorization: Bearer <token>` header.
3. Backend verifies JWT against Clerk JWKS and resolves the local `User` record.
4. `get_current_user` dependency enforces auth; `get_optional_user` allows anonymous access.

### Data Flow for a Ranking

1. Client requests a Roll (`/api/daily`, `/api/quickplay`, `/api/hoopiq`).
2. Backend selects players, persists the Roll, returns player data.
3. User submits ranking → backend computes Kendall tau distance against consensus → assigns letter grade.
4. Leaderboard scores and streaks are updated.

### Testing Conventions

- Tests live in `backend/tests/`.
- Tests are organized by domain: `test_scoring.py`, `test_rolls.py`, `test_streak.py`, etc.
- Use `pytest` with class-based test organization (`class TestXxx`).
- Hypothesis is available for property-based testing.
- Test fixtures use plain Python data (dicts/lists) rather than DB fixtures where possible.
