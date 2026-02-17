from functools import lru_cache

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import get_settings


@lru_cache
def get_engine():
    return create_async_engine(
        get_settings().database_url,
        pool_pre_ping=True,
    )


@lru_cache
def get_sessionmaker():
    return async_sessionmaker(
        bind=get_engine(),
        expire_on_commit=False,
    )
