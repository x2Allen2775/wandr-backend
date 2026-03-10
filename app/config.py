from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./wandr.db"
    SECRET_KEY: str = "changeme_in_production_please"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    APP_NAME: str = "Wandr"
    APP_ENV: str = "development"
    SENDGRID_API_KEY: str | None = None

    class Config:
        env_file = ".env"

settings = Settings()
