"""Async DB Session — PostgreSQL (Neon/Supabase compatible)."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)
_engine = None
_async_session_maker: Optional[async_sessionmaker[AsyncSession]] = None


async def init_db() -> None:
    global _engine, _async_session_maker
    if _engine is not None:
        return
    _engine = create_async_engine(
        settings.database_url, echo=False, pool_size=5, max_overflow=2,
        pool_pre_ping=True, pool_recycle=3600,
    )
    _async_session_maker = async_sessionmaker(bind=_engine, class_=AsyncSession, expire_on_commit=False)
    from src.db.models import Base
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database connected")


async def close_db() -> None:
    global _engine, _async_session_maker
    if _engine is None:
        return
    await _engine.dispose()
    _engine = None
    _async_session_maker = None


async def get_session() -> AsyncSession:
    if _async_session_maker is None:
        raise RuntimeError("DB not initialized")
    return _async_session_maker()


@asynccontextmanager
async def session_scope() -> AsyncGenerator[AsyncSession, None]:
    session = await get_session()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def health_check() -> bool:
    try:
        async with session_scope() as session:
            from sqlalchemy import text
            await session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False