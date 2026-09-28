from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./shopstream.db"
    AI_MODEL: str = "gemini-pro"  # Google's Gemini model
    GOOGLE_API_KEY: str = ""
    DEFAULT_STRATEGY: Literal["RULE_BASED", "AI_ADVISOR"] = "RULE_BASED"
    ALLOWED_ORIGINS: list[str] = ["*"]
    
    class Config:
        env_file = ".env"


settings = Settings()