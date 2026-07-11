"""
Зависимости для роутов: извлечение текущего пользователя из access-токена,
проверка ролей (модератор/админ), а также "опциональный" пользователь для
публичных эндпоинтов, которые по-разному ведут себя для гостя/владельца.
"""
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import RoleEnum
from app.database import get_db
from app.models import User
from app.security import TokenType, decode_token

# auto_error=False -> сами решаем, кидать 401 или трактовать как гостя
bearer_scheme = HTTPAuthorizationCredentials
_security = HTTPBearer(auto_error=False)


async def _load_user(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_security),
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется авторизация",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_token(credentials.credentials, TokenType.access)
    user = await _load_user(db, int(payload["sub"]))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Пользователь не найден")
    if user.is_banned:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Аккаунт заблокирован")
    return user


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_security),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    if credentials is None:
        return None
    try:
        payload = decode_token(credentials.credentials, TokenType.access)
    except HTTPException:
        return None
    user = await _load_user(db, int(payload["sub"]))
    if user is None or user.is_banned:
        return None
    return user


def require_roles(*roles: RoleEnum):
    async def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in [r.value for r in roles]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")
        return user

    return checker


require_moderator = require_roles(RoleEnum.moderator, RoleEnum.admin)
require_admin = require_roles(RoleEnum.admin)
