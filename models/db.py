# app/models/db.py
from __future__ import annotations

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from config import PG_DSN

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


class Base(DeclarativeBase):
    pass


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        # PG_DSN формата: postgresql+asyncpg://user:pass@host:port/db
        _engine = create_async_engine(PG_DSN, echo=False, pool_pre_ping=True)
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    global _sessionmaker
    if _sessionmaker is None:
        _sessionmaker = async_sessionmaker(get_engine(), expire_on_commit=False)
    return _sessionmaker


async def init_db():
    from .task import Category, Task, User  # импорт моделей

    async with get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
