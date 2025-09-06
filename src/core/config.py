from dataclasses import dataclass
from enum import IntEnum

import pytz
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL as db_url


class Enviroment(IntEnum):
    Development = 1
    Production = 2
    Testing = 3


class QueriesConnectionString(BaseModel):
    charset: str

@dataclass
class HashingSettings:
    iterations: int
    algorithm: str


class Settings(BaseSettings):
    MYSQL_RW_HOST: str = "127.0.0.1"
    MYSQL_RW_PORT: int = 3306

    MYSQL_RO_HOST: str = "127.0.0.1"
    MYSQL_RO_PORT: int = 3306

    FASTAPI_HOST: str = "127.0.0.1"
    FASTAPI_PORT: int = 8000

    GAMECORE_HOST: str = "127.0.0.1"
    GAMECORE_PORT: int = 31222
    # таймаут в секундах
    GAMECORE_TIMEOUT: int | float = 10

    MYSQL_ROOT_PASSWORD: str = ""
    MYSQL_USER: str = "user"
    MYSQL_PASSWORD: str = ""
    MYSQL_DATABASE: str = "arena_db"

    DROP_BEFORE: bool = False
    CLUSTER: bool = False
    LOG_LEVEL: str = "INFO"
    AUTO_BACKUP: bool = True

    # длительность указана в минутах
    ACCESS_TOKEN_LIFETIME: int = 15
    SESSION_LIFETIME: int = 24*60
    MAX_SESSIONS: int = 10

    ENVIROMENT: Enviroment = Enviroment.Development

    SECRET_KEY: str = ""

    model_config = SettingsConfigDict(
        env_file=(".env.dev", ".env"), env_file_encoding="utf-8"
    )


class Config:
    @classmethod
    def setup(cls, settings: Settings):
        cls.settings = settings

        cls.CONNECTION_URL_FASTAPI: str = (
            f"http://{settings.FASTAPI_HOST}:{settings.FASTAPI_PORT}/"
        )

        cls.CONNECTION_URL: db_url = db_url.create(
            drivername="mysql+aiomysql",
            username=settings.MYSQL_USER,
            password=settings.MYSQL_PASSWORD,
            host=settings.MYSQL_RW_HOST,
            port=settings.MYSQL_RW_PORT,
            database=settings.MYSQL_DATABASE,
            query=QUERIES.model_dump(),
        )

        cls.CONNECTION_URL_READ_ONLY: db_url = db_url.create(
            drivername="mysql+aiomysql",
            username=settings.MYSQL_USER,
            password=settings.MYSQL_PASSWORD,
            host=settings.MYSQL_RO_HOST,
            port=settings.MYSQL_RO_PORT,
            database=settings.MYSQL_DATABASE,
            query=QUERIES.model_dump(),
        )


QUERIES = QueriesConnectionString(charset="utf8mb4")

TIMEZONE = pytz.timezone("Europe/Moscow")

HASHING_SETTINGS = HashingSettings(
    iterations=4,  # дефолтное значение = 12, около 200-300 мс, увеличение на 1 дает удвоение времени
    algorithm="bcrypt",
)
