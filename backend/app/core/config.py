from pydantic_settings import BaseSettings
from typing import Optional
from urllib.parse import quote_plus
from pathlib import Path


class Settings(BaseSettings):
    # App
    APP_NAME: str = "ThePred API"
    DEBUG: bool = True
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # Database
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "thepred"
    POSTGRES_USER: str = "thepred"
    POSTGRES_PASSWORD: str = "changeme"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    # JWT
    JWT_SECRET: str = "your_super_secret_jwt_key"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 24

    # TON Blockchain Integration
    TON_API_KEY: str = ""  # Optional, for higher rate limits on tonapi.io
    TON_API_URL: str = "https://tonapi.io/v2"  # TON API endpoint
    TON_DEPOSIT_ADDRESS: str = ""  # Platform wallet address for deposits

    # TON Conversion & Limits
    TON_TO_PRED_RATE: int = 1000  # 1 TON = 1000 PRED
    MIN_DEPOSIT_TON: str = "0.1"  # Minimum deposit amount
    MAX_DEPOSIT_TON: str = "1000"  # Maximum deposit amount
    DEPOSIT_TIMEOUT_MINUTES: int = 30  # Time to complete deposit
    REQUIRED_CONFIRMATIONS: int = 1  # Blockchain confirmations required

    # Gamification
    INITIAL_PRED_BALANCE: int = 1000
    REFERRAL_BONUS_PRED: int = 100

    # Commission rates
    COMMISSION_PRED: float = 0.01  # 1%
    COMMISSION_TON: float = 0.05   # 5%

    # Sentry
    SENTRY_DSN: Optional[str] = None

    # S3 Storage
    S3_ENDPOINT: str = "http://minio:9000"
    S3_ACCESS_KEY: str = "admin"
    S3_SECRET_KEY: str = "Ivanbunin110818"
    S3_BUCKET: str = "thepred-events"
    S3_PUBLIC_URL: str = "https://thepred.store"

    # Telegram Bot
    BOT_TOKEN: Optional[str] = None
    WEBAPP_URL: str = "https://thepred.store"

    @property
    def database_url(self) -> str:
        password = quote_plus(self.POSTGRES_PASSWORD)
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{password}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def redis_url(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}"

    class Config:
        # Look for .env in project root (3 levels up: app -> backend -> root)
        env_file = str(Path(__file__).parent.parent.parent.parent / ".env")
        case_sensitive = True
        extra = 'ignore'  # Ignore extra fields from .env (for other services)


settings = Settings()
