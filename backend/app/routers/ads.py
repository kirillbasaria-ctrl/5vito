from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.constants import AdStatusEnum, CategoryEnum, CityEnum, RoleEnum
from app.database import get_db
from app.deps import get_current_user, get_optional_user
from app.models import Ad, AdImage, Favorite, User
from app.schemas import (
    AdCreateIn,
    AdImageOut,
    AdListItemOut,
    AdOut,
    AdPublishIn,
    AdUpdateIn,
    Page,
)
from app.utils import delete_upload_file, image_url, paginate_params, save_upload_file, total_pages

router = APIRouter(prefix="/api/ads", tags=["ads"])


def _ad_query_with_relations():
    return select(Ad).options(selectinload(Ad.owner), selectinload(Ad.images))


def _to_list_item(ad: Ad) -> AdListItemOut:
    cover = ad.images[0].filename if ad.images else None
    item = AdListItemOut.model_validate(ad)
    item.cover_image = image_url(cover) if cover else None
    return item


def _check_can_view(ad: Ad, user: User | None) -> None:
    if ad.status == AdStatusEnum.active.value:
        return
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Объявление не найдено")
    is_owner = ad.owner_id == user.id
    is_staff = user.role in (RoleEnum.moderator.value, RoleEnum.admin.value)
    if not (is_owner or is_staff):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Объявление не найдено")


def _check_can_edit(ad: Ad, user: User) -> None:
    if ad.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Это не ваше объявление")


async def _get_ad_or_404(db: AsyncSession, ad_id: int) -> Ad:
    result = await db.execute(_ad_query_with_relations().where(Ad.id == ad_id))
    ad = result.scalar_one_or_none()
    if ad is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Объявление не найдено")
    ad.is_favorited = False  # переопределяется явно там, где известен текущий пользователь
    return ad


@router.get("", response_model=Page[AdListItemOut])
async def list_ads(
    category: CategoryEnum | None = None,
    city: CityEnum | None = None,
    search: str | None = Query(default=None, max_length=150),
    min_price: float | None = Query(default=None, ge=0),
    max_price: float | None = Query(default=None, ge=0),
    owner_id: int | None = None,
    sort: str = Query(default="new", pattern="^(new|price_asc|price_desc)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=settings.DEFAULT_PAGE_SIZE, ge=1),
    db: AsyncSession = Depends(get_db),
):
    page, page_size = paginate_params(page, page_size)

    conditions = [Ad.status == AdStatusEnum.active.value]
    if category is not None:
        conditions.append(Ad.category == category.value)
    if city is not None:
        conditions.append(Ad.city == city.value)
    if owner_id is not None:
        conditions.append(Ad.owner_id == owner_id)
    if search:
        like = f"%{search.strip()}%"
        conditions.append(Ad.title.ilike(like))
    if min_price is not None:
        conditions.append(Ad.price >= min_price)
    if max_price is not None:
        conditions.append(Ad.price <= max_price)

    base_query = _ad_query_with_relations().where(and_(*conditions))

    if sort == "price_asc":
        base_query = base_query.order_by(Ad.price.asc().nulls_last())
    elif sort == "price_desc":
        base_query = base_query.order_by(Ad.price.desc().nulls_last())
    else:
        base_query = base_query.order_by(Ad.created_at.desc())

    count_result = await db.execute(select(func.count(Ad.id)).where(and_(*conditions)))
    total = count_result.scalar_one()

    paged_query = base_query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(paged_query)
    ads = result.scalars().all()

    return Page(
        items=[_to_list_item(ad) for ad in ads],
        total=total,
        page=page,
        page_size=page_size,
        pages=total_pages(total, page_size),
    )


@router.get("/mine", response_model=list[AdListItemOut])
async def list_my_ads(
    ad_status: AdStatusEnum | None = Query(default=None, alias="status"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conditions = [Ad.owner_id == user.id]
    if ad_status is not None:
        conditions.append(Ad.status == ad_status.value)
    else:
        conditions.append(Ad.status != AdStatusEnum.deleted.value)

    result = await db.execute(
        _ad_query_with_relations().where(and_(*conditions)).order_by(Ad.created_at.desc())
    )
    ads = result.scalars().all()
    return [_to_list_item(ad) for ad in ads]


@router.get("/{ad_id}", response_model=AdOut)
async def get_ad(ad_id: int, user: User | None = Depends(get_optional_user), db: AsyncSession = Depends(get_db)):
    ad = await _get_ad_or_404(db, ad_id)
    _check_can_view(ad, user)

    if ad.status == AdStatusEnum.active.value and (user is None or user.id != ad.owner_id):
        ad.views += 1
        await db.commit()
        await db.refresh(ad)

    is_favorited = False
    if user is not None:
        fav_result = await db.execute(
            select(Favorite.id).where(Favorite.user_id == user.id, Favorite.ad_id == ad.id)
        )
        is_favorited = fav_result.scalar_one_or_none() is not None

    # SQLAlchemy-модели не имеют слотов, поэтому можно временно навесить
    # вычисляемое поле перед сериализацией через Pydantic (from_attributes).
    ad.is_favorited = is_favorited
    return ad


@router.post("", response_model=AdOut, status_code=status.HTTP_201_CREATED)
async def create_ad(data: AdCreateIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    ad = Ad(
        title=data.title.strip(),
        description=data.description.strip(),
        price=data.price,
        category=data.category.value,
        city=data.city.value,
        status=AdStatusEnum.draft.value if data.is_draft else AdStatusEnum.active.value,
        owner_id=user.id,
    )
    db.add(ad)
    await db.commit()
    return await _get_ad_or_404(db, ad.id)


@router.patch("/{ad_id}", response_model=AdOut)
async def update_ad(
    ad_id: int, data: AdUpdateIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    ad = await _get_ad_or_404(db, ad_id)
    _check_can_edit(ad, user)

    if ad.status == AdStatusEnum.deleted.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Объявление удалено")

    # model_fields_set отличает "поле не передали" от "явно очистили null":
    # это важно для price, где null означает "цена договорная".
    provided = data.model_fields_set

    if "title" in provided and data.title is not None:
        ad.title = data.title.strip()
    if "description" in provided and data.description is not None:
        ad.description = data.description.strip()
    if "price" in provided:
        ad.price = data.price
    if "category" in provided and data.category is not None:
        ad.category = data.category.value
    if "city" in provided and data.city is not None:
        ad.city = data.city.value

    await db.commit()
    return await _get_ad_or_404(db, ad_id)


@router.post("/{ad_id}/publish", response_model=AdOut)
async def publish_ad(
    ad_id: int, data: AdPublishIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    ad = await _get_ad_or_404(db, ad_id)
    _check_can_edit(ad, user)

    if ad.status not in (AdStatusEnum.draft.value, AdStatusEnum.active.value):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Скрытое или удалённое объявление нельзя опубликовать напрямую",
        )

    ad.status = AdStatusEnum.draft.value if data.is_draft else AdStatusEnum.active.value
    await db.commit()
    return await _get_ad_or_404(db, ad_id)


@router.delete("/{ad_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ad(ad_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    ad = await _get_ad_or_404(db, ad_id)
    _check_can_edit(ad, user)
    ad.status = AdStatusEnum.deleted.value
    await db.commit()


@router.post("/{ad_id}/images", response_model=AdImageOut, status_code=status.HTTP_201_CREATED)
async def upload_ad_image(
    ad_id: int,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ad = await _get_ad_or_404(db, ad_id)
    _check_can_edit(ad, user)

    if len(ad.images) >= settings.MAX_IMAGES_PER_AD:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Максимум {settings.MAX_IMAGES_PER_AD} фото на объявление",
        )

    filename = await save_upload_file(file)
    image = AdImage(ad_id=ad.id, filename=filename, position=len(ad.images))
    db.add(image)
    await db.commit()
    await db.refresh(image)

    return AdImageOut(id=image.id, url=image_url(image.filename), position=image.position)


@router.delete("/{ad_id}/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ad_image(
    ad_id: int, image_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    ad = await _get_ad_or_404(db, ad_id)
    _check_can_edit(ad, user)

    image = next((img for img in ad.images if img.id == image_id), None)
    if image is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Фото не найдено")

    delete_upload_file(image.filename)
    await db.delete(image)
    await db.commit()
