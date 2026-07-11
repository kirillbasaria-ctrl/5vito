"""
Админ-панель на серверных шаблонах Jinja2.

Доступна модераторам и админам (роль admin дополнительно может менять роли
пользователей). Это отдельное серверное приложение внутри того же FastAPI —
использует cookie-сессии (см. app/admin/auth.py), а не JWT основного API.
"""
from pathlib import Path

from fastapi import APIRouter, Depends, Form, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.admin.auth import (
    COOKIE_NAME,
    create_session_token,
    get_admin_user,
    get_admin_user_strict,
)
from app.constants import (
    AD_STATUS_LABELS,
    AdStatusEnum,
    CATEGORY_LABELS,
    CITY_LABELS,
    COMPLAINT_REASON_LABELS,
    COMPLAINT_STATUS_LABELS,
    ComplaintStatusEnum,
    RoleEnum,
    ROLE_LABELS,
)
from app.database import get_db
from app.models import Ad, Complaint, Review, User
from app.security import verify_password

router = APIRouter(prefix="/admin", tags=["admin"])

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
templates.env.globals.update(
    ROLE_LABELS=ROLE_LABELS,
    AD_STATUS_LABELS=AD_STATUS_LABELS,
    CATEGORY_LABELS=CATEGORY_LABELS,
    CITY_LABELS=CITY_LABELS,
    COMPLAINT_REASON_LABELS=COMPLAINT_REASON_LABELS,
    COMPLAINT_STATUS_LABELS=COMPLAINT_STATUS_LABELS,
)


# --------------------------------------------------------------------------
# Вход / выход
# --------------------------------------------------------------------------

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {"error": None})


@router.post("/login", response_class=HTMLResponse)
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == email.strip().lower()))
    user = result.scalar_one_or_none()

    error = None
    if user is None or not verify_password(password, user.password_hash):
        error = "Неверный email или пароль"
    elif user.role not in (RoleEnum.moderator.value, RoleEnum.admin.value):
        error = "У этого аккаунта нет доступа к админ-панели"
    elif user.is_banned:
        error = "Аккаунт заблокирован"

    if error:
        return templates.TemplateResponse(request, "login.html", {"error": error}, status_code=401)

    response = RedirectResponse(url="/admin/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        COOKIE_NAME,
        create_session_token(user.id),
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 12,
    )
    return response


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/admin/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(COOKIE_NAME)
    return response


# --------------------------------------------------------------------------
# Дашборд
# --------------------------------------------------------------------------

@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    counts = {}
    for st in AdStatusEnum:
        r = await db.execute(select(func.count(Ad.id)).where(Ad.status == st.value))
        counts[st.value] = r.scalar_one()

    users_count = (await db.execute(select(func.count(User.id)))).scalar_one()
    new_complaints_count = (
        await db.execute(select(func.count(Complaint.id)).where(Complaint.status == ComplaintStatusEnum.new.value))
    ).scalar_one()

    recent_complaints = (
        await db.execute(
            select(Complaint)
            .options(selectinload(Complaint.ad), selectinload(Complaint.author))
            .order_by(Complaint.created_at.desc())
            .limit(5)
        )
    ).scalars().all()

    recent_ads = (
        await db.execute(
            select(Ad).options(selectinload(Ad.owner)).order_by(Ad.created_at.desc()).limit(5)
        )
    ).scalars().all()

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "admin": admin,
            "active": "dashboard",
            "counts": counts,
            "users_count": users_count,
            "new_complaints_count": new_complaints_count,
            "recent_complaints": recent_complaints,
            "recent_ads": recent_ads,
        },
    )


# --------------------------------------------------------------------------
# Объявления
# --------------------------------------------------------------------------

@router.get("/ads", response_class=HTMLResponse)
async def ads_list(
    request: Request,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
    ad_status: str = Query(default="", alias="status"),
    category: str = "",
    city: str = "",
    search: str = "",
    page: int = 1,
    msg: str = "",
):
    conditions = []
    if ad_status:
        conditions.append(Ad.status == ad_status)
    if category:
        conditions.append(Ad.category == category)
    if city:
        conditions.append(Ad.city == city)
    if search:
        conditions.append(Ad.title.ilike(f"%{search.strip()}%"))

    page = max(page, 1)
    page_size = 25

    query = select(Ad).options(selectinload(Ad.owner)).order_by(Ad.created_at.desc())
    if conditions:
        query = query.where(and_(*conditions))

    count_query = select(func.count(Ad.id))
    if conditions:
        count_query = count_query.where(and_(*conditions))
    total = (await db.execute(count_query)).scalar_one()

    result = await db.execute(query.offset((page - 1) * page_size).limit(page_size))
    ads = result.scalars().all()

    return templates.TemplateResponse(
        request,
        "ads.html",
        {
            "admin": admin,
            "active": "ads",
            "ads": ads,
            "filters": {"status": ad_status, "category": category, "city": city, "search": search},
            "page": page,
            "has_next": total > page * page_size,
            "has_prev": page > 1,
            "total": total,
            "msg": msg,
        },
    )


@router.get("/ads/{ad_id}", response_class=HTMLResponse)
async def ad_detail(
    ad_id: int, request: Request, admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Ad)
        .where(Ad.id == ad_id)
        .options(selectinload(Ad.owner), selectinload(Ad.images), selectinload(Ad.complaints))
    )
    ad = result.scalar_one_or_none()
    return templates.TemplateResponse(request, "ad_detail.html", {"admin": admin, "active": "ads", "ad": ad})


async def _set_ad_status(db: AsyncSession, ad_id: int, new_status: str) -> None:
    result = await db.execute(select(Ad).where(Ad.id == ad_id))
    ad = result.scalar_one_or_none()
    if ad is not None:
        ad.status = new_status
        await db.commit()


@router.post("/ads/{ad_id}/hide")
async def hide_ad(ad_id: int, admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    await _set_ad_status(db, ad_id, AdStatusEnum.hidden.value)
    return RedirectResponse(url=f"/admin/ads/{ad_id}?msg=Объявление+скрыто", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/ads/{ad_id}/unhide")
async def unhide_ad(ad_id: int, admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    await _set_ad_status(db, ad_id, AdStatusEnum.active.value)
    return RedirectResponse(
        url=f"/admin/ads/{ad_id}?msg=Объявление+снова+активно", status_code=status.HTTP_303_SEE_OTHER
    )


@router.post("/ads/{ad_id}/delete")
async def delete_ad(ad_id: int, admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    await _set_ad_status(db, ad_id, AdStatusEnum.deleted.value)
    return RedirectResponse(url=f"/admin/ads/{ad_id}?msg=Объявление+удалено", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/ads/{ad_id}/restore")
async def restore_ad(ad_id: int, admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    await _set_ad_status(db, ad_id, AdStatusEnum.active.value)
    return RedirectResponse(
        url=f"/admin/ads/{ad_id}?msg=Объявление+восстановлено", status_code=status.HTTP_303_SEE_OTHER
    )


# --------------------------------------------------------------------------
# Пользователи
# --------------------------------------------------------------------------

@router.get("/users", response_class=HTMLResponse)
async def users_list(
    request: Request,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
    search: str = "",
    role: str = "",
    msg: str = "",
):
    conditions = []
    if search:
        like = f"%{search.strip()}%"
        conditions.append((User.email.ilike(like)) | (User.name.ilike(like)))
    if role:
        conditions.append(User.role == role)

    query = select(User).order_by(User.created_at.desc())
    if conditions:
        query = query.where(and_(*conditions))

    result = await db.execute(query.limit(200))
    users = result.scalars().all()

    return templates.TemplateResponse(
        request,
        "users.html",
        {"admin": admin, "active": "users", "users": users, "filters": {"search": search, "role": role}, "msg": msg},
    )


@router.post("/users/{user_id}/role")
async def change_role(
    user_id: int,
    role: str = Form(...),
    admin: User = Depends(get_admin_user_strict),
    db: AsyncSession = Depends(get_db),
):
    if role in (r.value for r in RoleEnum):
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is not None:
            user.role = role
            await db.commit()
    return RedirectResponse(url="/admin/users?msg=Роль+обновлена", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/users/{user_id}/ban")
async def ban_user(user_id: int, admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is not None and user.role != RoleEnum.admin.value:
        user.is_banned = True
        await db.commit()
    return RedirectResponse(url="/admin/users?msg=Пользователь+заблокирован", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/users/{user_id}/unban")
async def unban_user(user_id: int, admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is not None:
        user.is_banned = False
        await db.commit()
    return RedirectResponse(url="/admin/users?msg=Пользователь+разблокирован", status_code=status.HTTP_303_SEE_OTHER)


# --------------------------------------------------------------------------
# Жалобы
# --------------------------------------------------------------------------

@router.get("/complaints", response_class=HTMLResponse)
async def complaints_list(
    request: Request,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
    complaint_status: str = "",
    msg: str = "",
):
    query = (
        select(Complaint)
        .options(selectinload(Complaint.ad), selectinload(Complaint.author))
        .order_by(Complaint.created_at.desc())
    )
    if complaint_status:
        query = query.where(Complaint.status == complaint_status)

    result = await db.execute(query.limit(200))
    complaints = result.scalars().all()

    return templates.TemplateResponse(
        request,
        "complaints.html",
        {
            "admin": admin,
            "active": "complaints",
            "complaints": complaints,
            "filters": {"status": complaint_status},
            "msg": msg,
        },
    )


@router.post("/complaints/{complaint_id}/resolve")
async def resolve_complaint(
    complaint_id: int, admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Complaint).where(Complaint.id == complaint_id))
    complaint = result.scalar_one_or_none()
    if complaint is not None:
        complaint.status = ComplaintStatusEnum.resolved.value
        complaint.resolved_by = admin.id
        from datetime import datetime, timezone

        complaint.resolved_at = datetime.now(timezone.utc)
        await db.commit()
    return RedirectResponse(url="/admin/complaints?msg=Жалоба+обработана", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/complaints/{complaint_id}/reject")
async def reject_complaint(
    complaint_id: int, admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Complaint).where(Complaint.id == complaint_id))
    complaint = result.scalar_one_or_none()
    if complaint is not None:
        complaint.status = ComplaintStatusEnum.rejected.value
        complaint.resolved_by = admin.id
        from datetime import datetime, timezone

        complaint.resolved_at = datetime.now(timezone.utc)
        await db.commit()
    return RedirectResponse(url="/admin/complaints?msg=Жалоба+отклонена", status_code=status.HTTP_303_SEE_OTHER)


# --------------------------------------------------------------------------
# Отзывы
# --------------------------------------------------------------------------

@router.get("/reviews", response_class=HTMLResponse)
async def reviews_list(
    request: Request, admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db), msg: str = ""
):
    result = await db.execute(
        select(Review)
        .options(selectinload(Review.author), selectinload(Review.target_user))
        .order_by(Review.created_at.desc())
        .limit(200)
    )
    reviews = result.scalars().all()
    return templates.TemplateResponse(
        request, "reviews.html", {"admin": admin, "active": "reviews", "reviews": reviews, "msg": msg}
    )


@router.post("/reviews/{review_id}/delete")
async def delete_review(review_id: int, admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Review).where(Review.id == review_id))
    review = result.scalar_one_or_none()
    if review is not None:
        await db.delete(review)
        await db.commit()
    return RedirectResponse(url="/admin/reviews?msg=Отзыв+удалён", status_code=status.HTTP_303_SEE_OTHER)
