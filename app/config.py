from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App settings. Values can be overridden by environment variables or a .env file."""

    database_url: str = "postgresql://postgres:postgres@localhost:5432/urlshortener"
    base_url: str = "http://localhost:8000"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()