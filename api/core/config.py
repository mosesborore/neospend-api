"""
Application configuration module.

Reads configuration from environment variables and .env file.
Supports different environments: development, testing, production.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel

# Load environment variables from .env file
BASE_DIR = Path(__file__).resolve().parent.parent.parent
env_file = BASE_DIR / ".env"
load_dotenv(env_file)


def get_environ():
    environ = os.getenv("ENVIRONMENT", "dev")

    if environ not in ["testing", "prod", "dev"]:
        raise ValueError(f"Misconfigured environment value: {str(environ)}. ")
    return environ


class Config(BaseModel):
    """Base configuration class."""

    ENVIRONMENT: str = get_environ()
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///database.db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    SQLALCHEMY_ECHO: bool = os.getenv("SQLALCHEMY_ECHO", "True").lower() in (
        "true",
        "1",
        "yes",
    )


class DevelopmentConfig(Config):
    """Development environment configuration."""

    DEBUG: bool = True
    SQLALCHEMY_ECHO: bool = True


class TestingConfig(Config):
    """Testing environment configuration."""

    ENVIRONMENT: str = "testing"
    DEBUG: bool = True
    DATABASE_URL: str = "sqlite:///test_database.db"
    SQLALCHEMY_ECHO: bool = False


class ProductionConfig(Config):
    """Production environment configuration."""

    DEBUG: bool = False
    SQLALCHEMY_ECHO: bool = False


def get_config() -> Config:
    """
    Get the appropriate configuration class based on ENVIRONMENT.

    Returns:
        Config: The configuration object for the current environment.
    """

    environment = os.getenv("ENVIRONMENT", "dev").lower()

    config_map = {
        "dev": DevelopmentConfig,
        "testing": TestingConfig,
        "prod": ProductionConfig,
    }

    config_class = config_map.get(environment, DevelopmentConfig)
    return config_class()


# Export configuration instance
settings = get_config()
