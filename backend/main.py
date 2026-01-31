import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from domain.settings import get_settings
from routers import auth, health

# Set auth mode from environment, default to mock for testing
os.environ.setdefault("AUTH_MODE", "mock")

settings = get_settings()

app = FastAPI(
    title="AlphaLens API",
    description="AI-powered stock analysis and recommendation platform",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
