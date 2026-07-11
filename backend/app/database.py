"""
Настройка асинхронного подключения к БД.

Поддерживает как SQLite (для локальной разработки "из коробки"), так и
Postgres/Supabase через asyncpg. Для Supabase важно:
  - использовать connection string с драйвером asyncpg:
    postgresql+asyncpg://postgres:PASSWORD@HOST:5432/postgres
  - при использовании Supabase connection pooler (pgbouncer, transaction
    mode) отключать prepared statement cache asyncpg, иначе будут ошибки
    "prepared statement ... already exists". Это учтено ниже.
"""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    pass


def _make_engine():
    connect_args: dict = {}
    url = settings.DATABASE_URL

    if url.startswith("postgresql+asyncpg"):
        if settings.DATABASE_SSL:
            connect_args["ssl"] = True
        if settings.DATABASE_DISABLE_STATEMENT_CACHE:
            # Критично для Supabase pgbouncer (transaction pooling mode).
            connect_args["statement_cache_size"] = 0

    return create_async_engine(
        url,
        echo=False,
        pool_pre_ping=True,
        connect_args=connect_args,
    )


engine = _make_engine()

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def init_models() -> None:
    """Создаёт таблицы напрямую из моделей (без alembic).

    Используется только если settings.AUTO_CREATE_TABLES=True — удобно для
    локального запуска. В проде накатывайте миграции через alembic.
    """
    # Импортируем модели, чтобы они зарегистрировались в Base.metadata.
    from app import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
