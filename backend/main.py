import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from domain.settings import get_settings
from routers import auth, health, recommendations

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()
logger.info(f"Starting with AUTH_MODE={settings.auth_mode}")

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
app.include_router(recommendations.router)
