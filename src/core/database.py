from src.core import custom_logging
from typing import Annotated

from fastapi import Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from src.core.config import Config, Settings


class Base(AsyncAttrs, DeclarativeBase):
    __tablename__: str


class Database:
    @classmethod
    def setup(cls, settings: Settings, config: Config):
        cls.settings = settings

        cls.expire_on_commit = False
        cls.autoflush = False

        cls.async_engine: AsyncEngine = create_async_engine(
            config.CONNECTION_URL,
            echo=True if settings.LOG_LEVEL == "DEBUG" else False,
            pool_recycle=280,
            echo_pool="debug" if settings.LOG_LEVEL == "DEBUG" else None,
            pool_pre_ping=True,
            isolation_level="REPEATABLE READ",
            hide_parameters=False if settings.LOG_LEVEL == "DEBUG" else True,
        )
        cls.SessionLocal = async_sessionmaker(
            cls.async_engine,
            expire_on_commit=cls.expire_on_commit,
            autoflush=cls.autoflush,
        )

        cls.read_only_async_engine: AsyncEngine = (
            create_async_engine(
                config.CONNECTION_URL_READ_ONLY,
                echo=True if settings.LOG_LEVEL == "DEBUG" else False,
                pool_reset_on_return=None,
                pool_recycle=280,
                echo_pool="debug" if settings.LOG_LEVEL == "DEBUG" else None,
                pool_pre_ping=True,
                isolation_level="REPEATABLE READ",
                hide_parameters=False if settings.LOG_LEVEL == "DEBUG" else True,
            )
            if cls.settings.CLUSTER
            else cls.async_engine
        )


async def get_db_session():
    async with Database.async_engine.begin() as conn:
        session = AsyncSession(
            conn,
            autoflush=Database.autoflush,
            expire_on_commit=Database.expire_on_commit,
        )
        try:
            yield session
        except Exception as exc:
            await session.rollback()
            custom_logging.exception(exc)
            raise exc
        else:
            await session.flush()


async def get_db_session_read_only():
    async with Database.async_engine.begin() as conn:
        await conn.execute(text("start transaction read only"))
        ro_session = AsyncSession(
            conn,
            autoflush=Database.autoflush,
            expire_on_commit=Database.expire_on_commit,
        )
        try:
            yield ro_session
        except Exception as exc:
            custom_logging.exception(exc)
            raise exc


DbSessionDep = Annotated[AsyncSession, Depends(get_db_session)]
DbSessionDepReadOnly = Annotated[AsyncSession, Depends(get_db_session_read_only)]
