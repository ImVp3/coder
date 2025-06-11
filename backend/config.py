from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "LearnDash LMS"
    
    # OpenAI Settings
    OPENAI_API_KEY: str
    SUPERVISOR_MODEL: str = "gemini-2.0-flash"
    WORKER_MODEL: str = "gemini-2.0-flash"
    
    # CORS Settings
    BACKEND_CORS_ORIGINS: list[str] = ["*"]
    
    # Database Settings (if needed later)
    DATABASE_URL: Optional[str] = None
    
    class Config:
        case_sensitive = True
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings() 