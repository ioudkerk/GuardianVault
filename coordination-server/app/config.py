from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application configuration settings"""

    # MongoDB
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "guardianvault"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True

    # Security
    secret_key: str = "dev-secret-key-change-in-production"

    # CORS
    cors_origins: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # MPC Protocol Timeouts
    signing_round_timeout: int = 300  # 5 minutes
    transaction_timeout: int = 3600  # 1 hour

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()
