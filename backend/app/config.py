from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    # App
    app_name: str = "ReCloud Lead Intelligence"
    app_env: str = "development"
    app_url: str = "http://localhost:3000"
    api_url: str = "http://localhost:8000"

    # Database / cache
    database_url: str = "postgresql://postgres:postgres@postgres:5432/recloud_leads"
    redis_url: str = "redis://redis:6379/0"

    # Auth
    jwt_secret: str = "replace_with_secure_random_string"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 1440

    # OpenAI-compatible AI
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4.1-mini"

    # Firecrawl
    firecrawl_api_key: str = ""
    firecrawl_base_url: str = "https://api.firecrawl.dev"

    # JobSpy
    jobspy_enabled: bool = True
    jobspy_default_country: str = "india"
    jobspy_default_results_limit: int = 100
    jobspy_proxies: str = ""

    # Email verification
    reacher_api_url: str = "http://reacher:8080"
    reacher_api_key: str = ""
    zerobounce_api_key: str = ""
    hunter_api_key: str = ""
    apollo_api_key: str = ""

    # CRM
    baserow_api_url: str = ""
    baserow_api_key: str = ""
    twenty_api_url: str = ""
    twenty_api_key: str = ""
    hubspot_api_key: str = ""

    # Webhook
    n8n_webhook_url: str = ""

    # SMTP
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""

    # Feature flags
    enable_contact_enrichment: bool = False
    enable_email_verification: bool = True
    enable_ai_outreach_generation: bool = True
    enable_csv_export: bool = True
    enable_crm_sync: bool = False
    enable_outreach_sending: bool = False

    @property
    def cors_origins(self) -> list[str]:
        return [self.app_url, "http://localhost:3000", "http://127.0.0.1:3000"]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
