from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator
from typing import Optional

# Use pydantic_settings for modern Pydantic versions
class Settings(BaseSettings):
    # Core Security
    SECRET_KEY: str = ""
    REFRESH_SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    # Redis Host (for Docker Compose, defaults to localhost for local development)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    # Celery
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None
    # Database
    DATABASE_URL: str = "sqlite:///./llm.db"

    # LLM Service
    OPENAI_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4o-mini"
    GOOGLE_API_KEY: str = ""
    GOOGLE_LLM_MODEL: str =  "gemini-2.5-flash"

    # Background Queue
    REDIS_URL: Optional[str] = None
    
    @model_validator(mode='after')
    def set_redis_urls(self):
        """Construct Redis URLs from REDIS_HOST if not explicitly set."""
        if self.CELERY_BROKER_URL is None:
            self.CELERY_BROKER_URL = f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"
        if self.CELERY_RESULT_BACKEND is None:
            self.CELERY_RESULT_BACKEND = f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"
        if self.REDIS_URL is None:
            self.REDIS_URL = f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}"
        return self

    # Configuration class for Pydantic Settings
    model_config = SettingsConfigDict(
        env_file=".env",
        extra='ignore' # Ignore extra fields in .env
    )

settings = Settings()