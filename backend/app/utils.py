"""Вспомогательные функции общего назначения."""
import math
import os
import uuid

from fastapi import HTTPException, UploadFile, status

from app.config import settings

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def paginate_params(page: int, page_size: int) -> tuple[int, int]:
    page = max(page, 1)
    page_size = max(1, min(page_size, settings.MAX_PAGE_SIZE))
    return page, page_size


def total_pages(total: int, page_size: int) -> int:
    return max(1, math.ceil(total / page_size)) if total else 1


async def save_upload_file(upload: UploadFile) -> str:
    """Сохраняет загруженное изображение в UPLOAD_DIR, возвращает имя файла."""
    if upload.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Разрешены только изображения JPEG, PNG или WEBP",
        )

    ext = os.path.splitext(upload.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        ext = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}[upload.content_type]

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    contents = await upload.read()
    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Файл слишком большой (максимум {settings.MAX_UPLOAD_SIZE_MB} МБ)",
        )

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{ext}"
    path = os.path.join(settings.UPLOAD_DIR, filename)
    with open(path, "wb") as f:
        f.write(contents)

    return filename


def delete_upload_file(filename: str) -> None:
    path = os.path.join(settings.UPLOAD_DIR, filename)
    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass


def image_url(filename: str) -> str:
    return f"/uploads/{filename}"
