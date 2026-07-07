from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str
    APP_VERSION: str
    DEBUG: bool
    MONGODB_URI: str
    DATABASE_NAME: str

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int
    REPOSITORIES_PATH: str
    LLM_PROVIDER: str = "groq"

    GROQ_API_KEY: Optional[str] = None

    GEMINI_API_KEY: Optional[str] = None
    EMBEDDING_PROVIDER: str = "gemini"


settings = Settings()