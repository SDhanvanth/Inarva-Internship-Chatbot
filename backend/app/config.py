"""
AI Platform Configuration
"""
import os
import secrets
from typing import List
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Application settings loaded from environment variables."""
    
    APP_NAME: str = os.getenv("APP_NAME", "Multi Chat AI")
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    WORKERS: int = int(os.getenv("WORKERS", "4"))
    
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
    DB_USER: str = os.getenv("DB_USER", "aiplatform")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_NAME: str = os.getenv("DB_NAME", "aiplatform")
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "20"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "10"))
    
    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property
    def DATABASE_URL_SYNC(self) -> str:
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    
    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
    ALLOWED_ORIGINS: List[str] = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
    API_KEY_HEADER: str = "X-API-Key"
    MCP_SIGNING_SECRET: str = os.getenv("MCP_SIGNING_SECRET", secrets.token_urlsafe(32))
    
    RATE_LIMIT_IP_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_IP_PER_MINUTE", "60"))
    RATE_LIMIT_IP_PER_HOUR: int = int(os.getenv("RATE_LIMIT_IP_PER_HOUR", "1000"))
    RATE_LIMIT_USER_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_USER_PER_MINUTE", "100"))
    RATE_LIMIT_USER_PER_HOUR: int = int(os.getenv("RATE_LIMIT_USER_PER_HOUR", "2000"))
    RATE_LIMIT_TOOL_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_TOOL_PER_MINUTE", "30"))
    RATE_LIMIT_BURST_SIZE: int = int(os.getenv("RATE_LIMIT_BURST_SIZE", "10"))
    
    MCP_DEFAULT_TIMEOUT: int = int(os.getenv("MCP_DEFAULT_TIMEOUT", "30"))
    MCP_MAX_RETRIES: int = int(os.getenv("MCP_MAX_RETRIES", "3"))
    MCP_RETRY_DELAY: float = float(os.getenv("MCP_RETRY_DELAY", "1.0"))
    
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = "gemini-3-flash-preview"
    INBUILT_MCP_ENABLED: bool = os.getenv("INBUILT_MCP_ENABLED", "true").lower() == "true"
    
    MAX_INPUT_LENGTH: int = int(os.getenv("MAX_INPUT_LENGTH", "50000"))
    MAX_CONVERSATION_MESSAGES: int = int(os.getenv("MAX_CONVERSATION_MESSAGES", "100"))
    
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", secrets.token_urlsafe(32))


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

settings = get_settings()
