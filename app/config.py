from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App settings. Values can be overridden by environment variables or a .env file."""

    database_url: str = "postgresql://postgres:postgres@localhost:5432/urlshortener"
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_seconds: int = 3600  # cached links expire after 1 hour
    base_url: str = "http://localhost:8000"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()