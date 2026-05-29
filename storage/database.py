from contextlib import asynccontextmanager, contextmanager
from functools import lru_cache
from typing import AsyncGenerator, Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker


def _to_async_url(database_url: str) -> str:
    if database_url.startswith("postgresql+psycopg2"):
        return database_url.replace("postgresql+psycopg2", "postgresql+asyncpg")
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+asyncpg://")
    return database_url


def _to_sync_url(database_url: str) -> str:
    if database_url.startswith("postgresql+asyncpg"):
        return database_url.replace("postgresql+asyncpg", "postgresql+psycopg2")
    return database_url


@lru_cache
def create_async_engine_from_url(database_url: str):
    async_url = _to_async_url(database_url)
    return create_async_engine(async_url, pool_pre_ping=True)


@lru_cache
def create_engine_from_url(database_url: str):
    sync_url = _to_sync_url(database_url)
    return create_engine(sync_url, pool_pre_ping=True)


@asynccontextmanager
async def get_async_session(database_url: str) -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine_from_url(database_url)
    session_local = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with session_local() as session:
        yield session


@contextmanager
def get_session(database_url: str) -> Generator:
    engine = create_engine_from_url(database_url)
    session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = session_local()
    try:
        yield session
    finally:
        session.close()
