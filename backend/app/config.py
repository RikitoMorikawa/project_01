from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Environment
    environment: str = os.getenv("ENVIRONMENT", "dev")
    
    # Database
    database_url: Optional[str] = None
    db_host: Optional[str] = None
    db_port: int = 3306
    db_name: Optional[str] = None
    db_user: Optional[str] = None
    db_password: Optional[str] = None
    
    # AWS
    aws_region: str = "ap-northeast-1"
    cognito_user_pool_id: Optional[str] = os.getenv("COGNITO_USER_POOL_ID")
    cognito_client_id: Optional[str] = os.getenv("COGNITO_CLIENT_ID")
    
    # Security
    jwt_secret_key: Optional[str] = os.getenv("JWT_SECRET_KEY")
    jwt_algorithm: str = "RS256"  # Cognito uses RS256
    
    # API
    api_title: str = "CSR Lambda API"
    api_version: str = "1.0.0"
    
    # CORS
    cors_origins: list = ["*"]
    
    class Config:
        env_file = f".env.{os.getenv('ENVIRONMENT', 'dev')}"
        env_file_encoding = 'utf-8'

# Global settings instance
settings = Settings()