import os
from pydantic_settings import BaseSettings

class DatabaseSettings(BaseSettings):
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///data/system.db")
    pool_size: int = 5
    max_overflow: int = 10
    pool_recycle: int = 1800

db_settings = DatabaseSettings()
