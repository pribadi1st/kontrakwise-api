import secrets
import warnings
from typing import Annotated, Any, Literal

from pydantic import (
    AnyUrl,
    BeforeValidator,
    EmailStr,
    HttpUrl,
    PostgresDsn,
    computed_field,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Self

class Settings(BaseSettings):
    # 1. Project Metadata
    PROJECT_NAME: str = "Contracts API"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    # 2. Database Configuration
    # We define individual components so it's easier to manage
    POSTGRES_HOST: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "contracts_db"
    POSTGRES_PORT: int = 5432

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        # This builds the string: postgresql+psycopg://user:pass@localhost:5432/db
        return f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # 3. Tell Pydantic to read from a .env file
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_ignore_empty=True, 
        extra="ignore"
    )

# Instantiate the settings so we can import 'settings' elsewhere
settings = Settings()