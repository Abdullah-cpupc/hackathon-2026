from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Database configuration
    database_url: str = "postgresql://postgres:postgres@localhost:5432/ai_chat_db"
    
    # Authentication
    secret_key: str = "your-secret-key-here-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Environment
    environment: str = "development"
    base_url: str = "http://localhost:8000"  # Base URL for file serving
    
    # Gemini API key (for LLM); supports GEMINI_API_KEY or GOOGLE_API_KEY env vars
    google_api_key: Optional[str] = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

# Try to load settings, fallback to defaults if .env is missing
try:
    settings = Settings()
except Exception as e:
    print(f"Warning: Could not load .env file: {e}")
    print("Using default settings. Please create a .env file with your configuration.")
    settings = Settings(
        database_url="postgresql://postgres:postgres@localhost:5432/ai_chat_db",
        secret_key="your-secret-key-here-change-in-production"
    )

