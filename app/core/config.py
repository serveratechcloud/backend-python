from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from functools import lru_cache

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "ISP Billing System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 30
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["https://serveratech.biz.id"]
    
    # Email
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    EMAIL_FROM: Optional[str] = None
    EMAIL_FROM_NAME: str = "ISP Billing System"
    
    # Payment Gateway
    PAYMENT_GATEWAY_URL: Optional[str] = None
    PAYMENT_GATEWAY_API_KEY: Optional[str] = None
    PAYMENT_GATEWAY_SECRET: Optional[str] = None
    PAYMENT_GATEWAY_WEBHOOK_SECRET: Optional[str] = None
    
    # MikroTik
    MIKROTIK_DEFAULT_PORT: int = 8728
    MIKROTIK_SSL_PORT: int = 8729
    MIKROTIK_TIMEOUT: int = 10
    
    # RADIUS
    RADIUS_SECRET: Optional[str] = None
    RADIUS_SERVER: str = "localhost"
    RADIUS_AUTH_PORT: int = 1812
    RADIUS_ACCT_PORT: int = 1813
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_RESULT_SERIALIZER: str = "json"
    CELERY_ACCEPT_CONTENT: List[str] = ["json"]
    CELERY_TIMEZONE: str = "Asia/Jakarta"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # Monitoring
    PROMETHEUS_PORT: int = 9090
    HEALTH_CHECK_INTERVAL: int = 30
    
    # File Storage
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10485760  # 10MB
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60
    
    # Backup
    BACKUP_SCHEDULE: str = "0 2 * * *"
    BACKUP_RETENTION_DAYS: int = 30
    BACKUP_PATH: str = "/var/backups/isp-billing"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
