from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    BACKEND_HOST: str = "localhost"
    BACKEND_PORT: int = 8000
    DEBUG: bool = True
    
    DATABASE_URL: str = "postgresql://mota_user:mota_password@localhost:5432/mota_sankalp"
    SQLALCHEMY_ECHO: bool = False
    
    SECRET_KEY: str = "dev-secret-key-change-in-production-minimum-32-characters"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    MAX_UPLOAD_SIZE_MB: int = 50
    UPLOAD_DIR: str = "./uploads"
    
    REDIS_URL: Optional[str] = None
    
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

settings = Settings()