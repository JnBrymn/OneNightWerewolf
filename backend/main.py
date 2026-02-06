import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from db.database import init_db
from api.game_sets import router as game_sets_router
from api.players import router as players_router
from api.games import router as games_router
# Import models to ensure they're registered with SQLAlchemy
from models import action  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    init_db()
    yield


app = FastAPI(
    title="One Night Werewolf API",
    version="1.0.0",
    lifespan=lifespan
)

# Include routers
app.include_router(game_sets_router)
app.include_router(players_router)
app.include_router(games_router)

# Get allowed origins from environment or default to localhost
allowed_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000"
).split(",")

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint to verify API is running."""
    return {"status": "healthy"}


@app.get("/ping")
async def ping():
    """Legacy ping endpoint for compatibility."""
    return {"message": "pong"}

