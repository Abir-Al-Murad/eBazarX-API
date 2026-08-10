from functools import lru_cache
from typing import Optional

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # ✅ Ignore extra fields from .env
    )

    # ==========================================================
    # Database
    # ==========================================================

    DATABASE_URL: str
    SYNC_DATABASE_URL: Optional[str] = None  # For Alembic

    # ==========================================================
    # Redis
    # ==========================================================

    REDIS_URL: str

    # ==========================================================
    # RabbitMQ
    # ==========================================================

    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672//"

    # ==========================================================
    # JWT
    # ==========================================================

    SECRET_KEY: SecretStr
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ==========================================================
    # Supabase
    # ==========================================================

    SUPABASE_URL: str
    SUPABASE_KEY: SecretStr
    SUPABASE_BUCKET: str = "ebazar-images"

    # ==========================================================
    # Payment Gateways
    # ==========================================================

    SSLCOMMERZ_STORE_ID: str = Field(...)
    SSLCOMMERZ_STORE_PASS: SecretStr = Field(...)
    SSLCOMMERZ_BASE_URL: str = "https://sandbox.sslcommerz.com"
    STRIPE_SECRET_KEY: Optional[SecretStr] = None
    SSLCOMMERZ_SANDBOX_MODE: bool = True   # ✅ ADD THIS
    BKAISH_API_KEY: Optional[SecretStr] = None  # ✅ Add for bKash

    # ==========================================================
    # Email
    # ==========================================================

    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[SecretStr] = None

    # ==========================================================
    # Celery
    # ==========================================================

    CELERY_BROKER_URL: str = "amqp://guest:guest@localhost:5672//"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # ==========================================================
    # Cloudinary
    # ==========================================================

    CLOUDINARY_CLOUD_NAME: str = Field(...)
    CLOUDINARY_API_KEY: str = Field(...)
    CLOUDINARY_API_SECRET: SecretStr = Field(...)
    CLOUDINARY_UPLOAD_FOLDER: str = "ebazar"
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024  # 5 MB



    STRIPE_SECRET_KEY: Optional[SecretStr] = None
    STRIPE_PUBLISHABLE_KEY: Optional[str] = None
    
    


@lru_cache
def get_settings() -> Settings:
    return Settings() # type: ignore


settings = get_settings()