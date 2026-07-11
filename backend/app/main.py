"""
Точка входа приложения.

Собирает вместе:
  - REST API под /api/* (для фронтенда-SPA)
  - Админ-панель на Jinja2 под /admin/*
  - Раздачу загруженных изображений под /uploads/*
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.admin.auth import AdminAuthRequired, AdminForbidden
from app.admin.router import router as admin_router
from app.config import settings
from app.database import init_models
from app.routers.ads import router as ads_router
from app.routers.auth import router as auth_router
from app.routers.complaints import router as complaints_router
from app.routers.favorites import router as favorites_router
from app.routers.meta import router as meta_router
from app.routers.reviews import router as reviews_router
from app.routers.users import router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.AUTO_CREATE_TABLES:
        await init_models()
    yield


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    # Аутентификация REST API — через заголовок Authorization: Bearer,
    # а не куки, поэтому allow_credentials не нужен (и не мешает работать
    # с allow_origins=["*"] при локальной разработке).
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Статика: загруженные фото объявлений и CSS админки ---
import os

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")
app.mount("/admin/static", StaticFiles(directory="app/admin/static"), name="admin_static")

# --- REST API ---
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(ads_router)
app.include_router(favorites_router)
app.include_router(reviews_router)
app.include_router(complaints_router)
app.include_router(meta_router)

# --- Админ-панель ---
app.include_router(admin_router)


@app.exception_handler(AdminAuthRequired)
async def admin_auth_required_handler(request: Request, exc: AdminAuthRequired):
    return RedirectResponse(url="/admin/login", status_code=303)


@app.exception_handler(AdminForbidden)
async def admin_forbidden_handler(request: Request, exc: AdminForbidden):
    return HTMLResponse("<h1>403</h1><p>Недостаточно прав для этого действия.</p>", status_code=403)


@app.get("/", tags=["health"])
async def root():
    return {"name": settings.APP_NAME, "status": "ok", "docs": "/docs", "admin": "/admin"}


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}
