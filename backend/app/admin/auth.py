"""
Аутентификация админ-панели.

Сознательно НЕ переиспользует JWT access/refresh из основного API: админка —
классическое серверное приложение на Jinja2 (формы, редиректы), поэтому
проще и надёжнее использовать подписанную httponly-cookie с ограниченным
временем жизни (itsdangerous), которая проверяется на каждый запрос.
"""
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.constants import RoleEnum
from app.database import get_db
from app.models import User

COOKIE_NAME = "admin_session"

_serializer = URLSafeTimedSerializer(settings.ADMIN_SESSION_SECRET, salt="admin-session")


class AdminAuthRequired(Exception):
    """Нет валидной сессии — нужно показать редирект на страницу входа."""


class AdminForbidden(Exception):
    """Есть сессия, но роли не хватает для действия (например, смена ролей)."""


def create_session_token(user_id: int) -> str:
    return _serializer.dumps({"user_id": user_id})


def _read_session_token(token: str) -> int | None:
    try:
        data = _serializer.loads(token, max_age=settings.ADMIN_SESSION_MAX_AGE_SECONDS)
    except (BadSignature, SignatureExpired):
        return None
    return data.get("user_id")


async def get_admin_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    token = request.cookies.get(COOKIE_NAME)
    user_id = _read_session_token(token) if token else None
    if user_id is None:
        raise AdminAuthRequired()

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or user.is_banned or user.role not in (RoleEnum.moderator.value, RoleEnum.admin.value):
        raise AdminAuthRequired()
    return user


async def get_admin_user_strict(user: User = Depends(get_admin_user)) -> User:
    """Требует именно роль admin (для смены ролей других пользователей)."""
    if user.role != RoleEnum.admin.value:
        raise AdminForbidden()
    return user
