"""
Создаёт (или повышает до admin) пользователя — нужно один раз после первого
деплоя, чтобы получить доступ в /admin, т.к. обычная регистрация всегда
создаёт роль "user".

Использование (из папки backend, с активированным venv):
    python -m scripts.create_admin admin@example.com StrongPass123 "Имя Фамилия"

На Render: Shell -> выполнить ту же команду.
"""
import asyncio
import sys

sys.path.insert(0, ".")

from sqlalchemy import select  # noqa: E402

from app.constants import RoleEnum  # noqa: E402
from app.database import AsyncSessionLocal, init_models  # noqa: E402
from app.models import User  # noqa: E402
from app.security import hash_password  # noqa: E402


async def main(email: str, password: str, name: str) -> None:
    await init_models()

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == email.lower()))
        user = result.scalar_one_or_none()

        if user is not None:
            user.role = RoleEnum.admin.value
            user.is_banned = False
            await db.commit()
            print(f"Пользователь {email} уже существовал — роль обновлена на admin.")
            return

        user = User(
            email=email.lower(),
            password_hash=hash_password(password),
            name=name,
            role=RoleEnum.admin.value,
        )
        db.add(user)
        await db.commit()
        print(f"Создан администратор {email}.")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Использование: python -m scripts.create_admin <email> <пароль> <имя>")
        sys.exit(1)

    asyncio.run(main(sys.argv[1], sys.argv[2], sys.argv[3]))
