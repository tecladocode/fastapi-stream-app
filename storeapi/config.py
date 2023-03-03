# Most of this taken from Redowan Delowar's post on configurations with Pydantic
# https://rednafi.github.io/digressions/python/2020/06/03/python-configs.html
from functools import lru_cache
from typing import Optional

from pydantic import BaseSettings, Field


class BaseConfig(BaseSettings):
    ENV_STATE: Optional[str] = Field(None, env="ENV_STATE")

    class Config:
        """Loads the dotenv file. Including this is necessary to get
        pydantic to load a .env file."""

        env_file: str = ".env"


class GlobalConfig(BaseConfig):
    DATABASE_URL: Optional[str] = None
    DB_FORCE_ROLL_BACK: bool = False
    B2_KEY_ID: Optional[str] = None
    B2_APPLICATION_KEY: Optional[str] = None
    B2_BUCKET_NAME: Optional[str] = None
    MAILGUN_DOMAIN: Optional[str] = None
    MAILGUN_API_KEY: Optional[str] = None
    LOGTAIL_API_KEY: Optional[str] = None


class DevConfig(GlobalConfig):
    class Config:
        env_prefix: str = "DEV_"


class ProdConfig(GlobalConfig):
    class Config:
        env_prefix: str = "PROD_"


class TestConfig(GlobalConfig):
    DATABASE_URL = "sqlite:///test.db"
    DB_FORCE_ROLL_BACK = True

    class Config:
        env_prefix: str = "TEST_"


@lru_cache()
def get_config(env_state):
    """Instantiate config based on the environment."""
    configs = {"dev": DevConfig, "prod": ProdConfig, "test": TestConfig}
    return configs[env_state]()


config = get_config(BaseConfig().ENV_STATE)
