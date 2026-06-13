import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, campaigns, dashboard, export, leads, settings as settings_routes
from app.config import settings

logging.basicConfig(level=logging.INFO)

app = FastAPI(title=settings.app_name, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=r"http://localhost:\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(campaigns.router)
app.include_router(leads.router)
app.include_router(dashboard.router)
app.include_router(settings_routes.router)
app.include_router(export.router)


@app.get("/")
def root() -> dict:
    return {"app": settings.app_name, "status": "ok", "docs": "/docs"}


@app.get("/api/health")
def health() -> dict:
    return {"status": "healthy", "env": settings.app_env}


@app.get("/api/config")
def public_config() -> dict:
    """Non-sensitive feature flags for the frontend."""
    return {
        "app_name": settings.app_name,
        "features": {
            "csv_export": settings.enable_csv_export,
            "ai_outreach_generation": settings.enable_ai_outreach_generation,
            "email_verification": settings.enable_email_verification,
            "crm_sync": settings.enable_crm_sync,
            "contact_enrichment": settings.enable_contact_enrichment,
            "outreach_sending": settings.enable_outreach_sending,
        },
    }
