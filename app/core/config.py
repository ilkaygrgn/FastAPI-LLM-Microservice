from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

# Use pydantic_settings for modern Pydantic versions
class Settings(BaseSettings):
    # Core Security
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Database
    DATABASE_URL: str = "sqlite:///./llm.db"

    # LLM Service
    OPENAI_API_KEY: str = ""

    # Background Queue
    REDIS_URL: str = "redis://localhost:6379"

    # Configuration class for Pydantic Settings
    model_config = SettingsConfigDict(
        env_file=".env",
        extra='ignore' # Ignore extra fields in .env
    )

settings = Settings()