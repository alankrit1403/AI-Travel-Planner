import os
from typing import Optional
from pydantic import ConfigDict
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "AI Travel Planner"
    DEBUG: bool = True
    
    # LLM Settings
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", "")
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    
    # Search API Keys
    SERPER_API_KEY: Optional[str] = os.getenv("SERPER_API_KEY", "")
    EXA_API_KEY: Optional[str] = os.getenv("EXA_API_KEY", "")
    TAVILY_API_KEY: Optional[str] = os.getenv("TAVILY_API_KEY", "")
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    model_config = ConfigDict(env_file=".env", extra="ignore")

settings = Settings()
