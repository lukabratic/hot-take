# Tech Stack & Build System

## Backend

- **Language**: Python 3.11+
- **Framework**: FastAPI (0.111.0)
- **ORM**: SQLAlchemy 2.0 with async support (`asyncpg`)
- **Migrations**: Alembic
- **Validation/Config**: Pydantic v2, pydantic-settings
- **Cache**: Redis (async via `redis` package)
- **Auth**: Clerk JWT verification using `python-jose`
- **HTTP Client**: httpx (async)
- **Testing**: pytest, pytest-asyncio, Hypothesis (property-based testing)
- **Data Pipeline**: nba_api, kagglehub, pandas

## Frontend

- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **Drag & Drop**: @dnd-kit
- **Animations**: Framer Motion
- **Auth**: Clerk (@clerk/*)

## Infrastructure

- **Database**: PostgreSQL 14+
- **Cache**: Redis 7+
- **Deployment**: Railway (backend via Procfile)
- **Server**: Uvicorn

## Common Commands

### Backend

```bash
# Install dependencies
pip install -r backend/requirements.txt

# Run database migrations
cd backend && alembic upgrade head

# Seed player data
cd backend && python -m pipeline.seed

# Start development server
cd backend && uvicorn main:app --reload --port 8000

# Run tests
cd backend && python -m pytest tests/ -v
```

### Frontend

```bash
# Install dependencies
cd frontend && npm install

# Start dev server (proxies /api to backend:8000)
cd frontend && npm run dev

# Type check
cd frontend && npx tsc --noEmit

# Production build
cd frontend && npm run build
```

## Environment Variables

### Backend (`backend/.env`)

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | PostgreSQL asyncpg connection string |
| `REDIS_URL` | Redis connection string |
| `CLERK_ISSUER` | Clerk JWT issuer URL |
| `CLERK_JWKS_URL` | Clerk JWKS endpoint for signature verification |
| `FRONTEND_ORIGIN` | Allowed CORS origin |

### Frontend (`frontend/.env`)

| Variable | Purpose |
|----------|---------|
| `VITE_CLERK_PUBLISHABLE_KEY` | Clerk publishable key |
