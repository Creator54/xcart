from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str = "don't tell anyone"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    DATABASE_URL: str = "sqlite:///./xcart.db"

settings = Settings()
