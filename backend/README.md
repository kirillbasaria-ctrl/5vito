# Бэкенд — Доска объявлений Вологодской области

FastAPI + SQLAlchemy 2.0 (async) + PostgreSQL (Supabase) / SQLite (локально) +
JWT-аутентификация + встроенная админ-панель на Jinja2.

## Стек

- Python 3.11+
- FastAPI, Pydantic v2
- SQLAlchemy 2.0 (async) + asyncpg (Postgres) / aiosqlite (SQLite, для локальной разработки)
- Alembic — миграции
- PyJWT — access/refresh токены
- Jinja2 — серверные шаблоны админ-панели
- bcrypt — хэширование паролей

## Структура

```
backend/
  app/
    main.py            # точка входа, роутеры, CORS, статика
    config.py           # настройки (переменные окружения)
    constants.py         # категории, города, роли, статусы (справочники)
    database.py          # async engine/session
    models.py             # SQLAlchemy-модели
    schemas.py             # Pydantic-схемы
    security.py             # хэши паролей, JWT
    deps.py                  # FastAPI-зависимости (текущий пользователь, роли)
    utils.py                  # пагинация, загрузка файлов
    routers/                   # REST API: auth, users, ads, favorites, reviews, complaints, meta
    admin/                       # админ-панель (Jinja2): роуты, шаблоны, статика
  alembic/                        # миграции БД
  scripts/create_admin.py          # создать/повысить пользователя до admin
  requirements.txt
  render.yaml                        # Render Blueprint
  .env.example
```

## Локальный запуск

По умолчанию используется локальный SQLite-файл — Postgres не нужен, чтобы
просто попробовать проект.

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env             # необязательно, но рекомендуется

uvicorn app.main:app --reload --port 8000
```

Таблицы создадутся автоматически при старте (`AUTO_CREATE_TABLES=true` по
умолчанию). Открыть:
- API: http://127.0.0.1:8000/docs (Swagger)
- Админка: http://127.0.0.1:8000/admin/login

Создать первого администратора (без него в `/admin` попасть нельзя, т.к.
обычная регистрация всегда создаёт роль `user`):

```bash
python -m scripts.create_admin admin@example.com StrongPass123 "Имя Фамилия"
```

Теперь можно войти в http://127.0.0.1:8000/admin/login этими данными.

## Переменные окружения

См. `.env.example` — там есть комментарии к каждой настройке. Главные:

| Переменная | Назначение |
|---|---|
| `DATABASE_URL` | Строка подключения к БД. По умолчанию SQLite. Для Supabase: `postgresql+asyncpg://...` |
| `JWT_SECRET_KEY` | Секрет для подписи JWT. **Обязательно смените в проде.** |
| `ADMIN_SESSION_SECRET` | Секрет для cookie-сессии админки. **Обязательно смените в проде.** |
| `CORS_ORIGINS` | Домен(ы) фронтенда через запятую (для GitHub Pages) |
| `AUTO_CREATE_TABLES` | `true` — создавать таблицы напрямую из моделей (удобно локально). В проде используйте `false` + `alembic upgrade head` |

## Миграции (Alembic)

```bash
# создать новую миграцию после изменения models.py
alembic revision --autogenerate -m "описание изменений"

# применить миграции
alembic upgrade head
```

Первая миграция (`alembic/versions/..._initial_schema.py`) уже создана и
описывает всю схему БД — только применить её на новой базе.

---

## Деплой: Supabase (БД) + Render (бэкенд) + GitHub Pages (фронтенд)

Всё бесплатно (в рамках free-тарифов каждого сервиса).

### 1. Supabase — создать Postgres-базу

1. Зарегистрируйтесь на https://supabase.com и создайте новый проект
   (Free plan). Задайте надёжный database password — он понадобится.
2. Дождитесь, пока проект поднимется (1-2 минуты).
3. Зайдите в **Project Settings → Database → Connection string**.
   Выберите вкладку **URI** и режим **Session pooler** (порт `5432`) либо
   **Transaction pooler** (порт `6543`) — оба работают с этим проектом,
   пуллер рекомендуется, т.к. у бесплатного плана Supabase ограничение на
   число прямых подключений.
4. Скопируйте connection string вида:
   ```
   postgresql://postgres.xxxxxxxx:[YOUR-PASSWORD]@aws-0-region.pooler.supabase.com:5432/postgres
   ```
5. Замените префикс `postgresql://` на `postgresql+asyncpg://` и подставьте
   свой пароль вместо `[YOUR-PASSWORD]`. Это и есть значение для `DATABASE_URL`.

### 2. Render — задеплоить бэкенд

**Вариант А — Blueprint (проще):**

1. Запушьте этот проект в свой GitHub-репозиторий.
2. На https://render.com → **New → Blueprint**, выберите репозиторий.
   Render найдёт `backend/render.yaml` и предложит создать сервис.
3. При создании попросит указать значения для переменных с `sync: false`:
   - `DATABASE_URL` — строка из шага 1 (с `+asyncpg`)
   - `CORS_ORIGINS` — адрес вашего GitHub Pages, например
     `https://your-username.github.io`
4. Нажмите **Apply** — Render соберёт и задеплоит сервис.

**Вариант Б — вручную:**

1. **New → Web Service**, подключите репозиторий.
2. **Root Directory**: `backend`
3. **Runtime**: Python 3
4. **Build Command**: `pip install -r requirements.txt`
5. **Start Command**: `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. Добавьте переменные окружения (Environment):
   - `DATABASE_URL` = строка подключения Supabase (`postgresql+asyncpg://...`)
   - `DATABASE_SSL` = `true`
   - `DATABASE_DISABLE_STATEMENT_CACHE` = `true`
   - `AUTO_CREATE_TABLES` = `false`
   - `JWT_SECRET_KEY` = сгенерируйте длинную случайную строку
   - `ADMIN_SESSION_SECRET` = сгенерируйте ещё одну
   - `CORS_ORIGINS` = адрес вашего фронтенда на GitHub Pages
7. Создайте сервис. После первого успешного деплоя откройте
   **Shell** (вкладка в сервисе на Render) и создайте админа:
   ```bash
   python -m scripts.create_admin admin@example.com StrongPass123 "Имя Фамилия"
   ```

Ваш бэкенд будет доступен по адресу вида
`https://vologda-ads-backend.onrender.com`. Проверьте:
`https://vologda-ads-backend.onrender.com/health` → `{"status":"ok"}`.

> **Про бесплатный тариф Render:** сервис "засыпает" при простое и
> "просыпается" ~30-50 секунд при первом запросе. Также локальная папка
> `uploads/` на free-тарифе не сохраняется между деплоями/перезапусками
> (эфемерная файловая система) — для продакшена стоит подключить внешнее
> хранилище (например, Supabase Storage или S3-совместимое); в текущем
> виде фото при передеплое будут потеряны, что и оговорено в ТЗ.

### 3. Фронтенд — GitHub Pages

См. `frontend/README.md`. Коротко: в `frontend/js/config.js` укажите адрес
вашего бэкенда на Render, затем включите GitHub Pages для папки `frontend/`
(или для ветки `gh-pages`) в настройках репозитория.

### 4. Проверка после деплоя

1. Откройте фронтенд на GitHub Pages — должен загрузиться список объявлений
   (изначально пустой).
2. Зарегистрируйте пользователя, создайте объявление.
3. Зайдите в `https://ваш-бэкенд.onrender.com/admin/login` под
   администратором — объявление должно быть видно в разделе "Объявления".
