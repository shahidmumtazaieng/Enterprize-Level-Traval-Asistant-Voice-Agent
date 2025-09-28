import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    LOG_LEVEL: int = 20  # INFO level
    
    # LiveKit settings
    LIVEKIT_API_KEY: str
    LIVEKIT_API_SECRET: str
    LIVEKIT_URL: str
    
    # AI Service settings
    PINECONE_API_KEY: Optional[str] = None
    ASSISTANT_NAME: Optional[str] = None
    
    # Google settings
    GOOGLE_API_KEY: str
    
    # Deepgram settings
    DEEPGRAM_API_KEY: str
    
    # Cartesia settings
    CARTESIA_API_KEY: str
    
    # Anam AI settings
    ANAM_API_KEY: Optional[str] = None
    ANAM_AVATAR_ID: Optional[str] = None
    AVATAR_IMAGE_PATH: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()