"""
Конфигурация приложения. Все настройки читаются из переменных окружения
(см. .env.example). Для локальной разработки без Postgres по умолчанию
используется SQLite (aiosqlite) — этого достаточно, чтобы поднять проект
и потыкать API без установки Postgres.

В проде (Render + Supabase) DATABASE_URL указывает на Postgres:
    postgresql+asyncpg://postgres:PASSWORD@HOST:5432/postgres
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Общее ---
    APP_NAME: str = "Доска объявлений Вологодской области"
    ENVIRONMENT: str = "development"  # development | production
    DEBUG: bool = True

    # --- База данных ---
    # По умолчанию — локальный SQLite-файл, чтобы проект запускался "из коробки".
    DATABASE_URL: str = "sqlite+aiosqlite:///./dev.db"
    # Включить SSL для подключения к Postgres (нужно для Supabase).
    DATABASE_SSL: bool = False
    # Отключает кэш prepared statements asyncpg — обязательно при подключении
    # через Supabase connection pooler (pgbouncer, transaction mode), иначе
    # можно словить ошибки вида "prepared statement already exists".
    DATABASE_DISABLE_STATEMENT_CACHE: bool = True
    # Создавать таблицы через Base.metadata.create_all при старте (удобно для
    # быстрого локального запуска без alembic). В проде держите False и
    # накатывайте миграции через `alembic upgrade head`.
    AUTO_CREATE_TABLES: bool = True

    # --- JWT ---
    JWT_SECRET_KEY: str = "change-me-in-production-please"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # --- Сессии админ-панели ---
    ADMIN_SESSION_SECRET: str = "change-me-admin-secret"
    ADMIN_SESSION_MAX_AGE_SECONDS: int = 60 * 60 * 12  # 12 часов

    # --- CORS ---
    # Список источников фронтенда через запятую, например:
    # https://username.github.io,http://localhost:5500
    CORS_ORIGINS: str = "*"

    # --- Загрузка файлов ---
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_MB: int = 5
    MAX_IMAGES_PER_AD: int = 6

    # --- Пагинация ---
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 50

    @property
    def cors_origins_list(self) -> list[str]:
        if self.CORS_ORIGINS.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
