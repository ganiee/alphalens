from fastapi import FastAPI

from routers import health

app = FastAPI(
    title="AlphaLens API",
    description="AI-powered stock analysis and recommendation platform",
    version="0.1.0",
)

app.include_router(health.router)
