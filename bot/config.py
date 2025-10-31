import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    WEBAPP_URL = os.getenv("WEBAPP_URL", "https://your-domain.com")
    API_URL = os.getenv("API_URL", "http://localhost:8000")

    # Database
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))
    POSTGRES_DB = os.getenv("POSTGRES_DB", "thepred")
    POSTGRES_USER = os.getenv("POSTGRES_USER", "thepred")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "changeme")

    # Redis
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

    @property
    def database_url(self):
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


config = Config()
