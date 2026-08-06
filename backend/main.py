from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from auth.router import router as auth_router
from rolls.router import router as rolls_router
from rolls.categories_router import router as categories_router
from rankings.router import router as rankings_router
from streak.router import router as streak_router
from leaderboard.router import router as leaderboard_router
from debate.router import router as debate_router
from profile.router import router as profile_router

app = FastAPI(
    title="Hot Take NBA Ranking Game API",
    description="Backend API for the Hot Take NBA Ranking Game",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(rolls_router)
app.include_router(categories_router)
app.include_router(rankings_router)
app.include_router(streak_router)
app.include_router(leaderboard_router)
app.include_router(debate_router)
app.include_router(profile_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
