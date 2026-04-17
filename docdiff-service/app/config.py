from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Service
    host: str = "0.0.0.0"
    port: int = 8000
    env: str = "development"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/avy_erp"
    database_schema: str = "docdiff"

    # Redis
    redis_url: str = "redis://localhost:6379/2"

    # Auth
    jwt_secret: str = ""

    # Storage
    storage_path: str = "./storage"

    # AI Providers
    anthropic_api_key: str = ""
    google_api_key: str = ""
    openrouter_api_key: str = ""
    qwen_local_endpoint: str = "http://localhost:8080/v1"

    # AI Defaults
    default_provider: str = "google"
    default_model: str = "gemini-2.5-flash"
    confidence_threshold: float = 0.75
    auto_confirm_threshold: float = 0.95
    page_render_dpi: int = 250

    # Processing
    max_pages: int = 20
    max_file_size_mb: int = 50
    max_retries: int = 3
    retry_backoff_base: int = 1

    model_config = {
        "env_prefix": "DOCDIFF_",
        "env_file": ".env",
        "extra": "ignore",
    }


class JWTSettings(BaseSettings):
    jwt_secret: str = ""

    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }


class AIKeySettings(BaseSettings):
    anthropic_api_key: str = ""
    google_api_key: str = ""
    openrouter_api_key: str = ""

    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }


def get_settings() -> Settings:
    base = Settings()
    jwt = JWTSettings()
    ai = AIKeySettings()
    if not base.jwt_secret and jwt.jwt_secret:
        base.jwt_secret = jwt.jwt_secret
    if not base.anthropic_api_key and ai.anthropic_api_key:
        base.anthropic_api_key = ai.anthropic_api_key
    if not base.google_api_key and ai.google_api_key:
        base.google_api_key = ai.google_api_key
    if not base.openrouter_api_key and ai.openrouter_api_key:
        base.openrouter_api_key = ai.openrouter_api_key
    return base


settings = get_settings()
