from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.deps import get_current_user
from app.models import Ad, Favorite, User
from app.schemas import AdListItemOut
from app.utils import image_url

router = APIRouter(prefix="/api/favorites", tags=["favorites"])


@router.get("", response_model=list[AdListItemOut])
async def list_favorites(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Ad)
        .join(Favorite, Favorite.ad_id == Ad.id)
        .where(Favorite.user_id == user.id)
        .options(selectinload(Ad.images), selectinload(Ad.owner))
        .order_by(Favorite.created_at.desc())
    )
    ads = result.scalars().all()
    items = []
    for ad in ads:
        item = AdListItemOut.model_validate(ad)
        item.cover_image = image_url(ad.images[0].filename) if ad.images else None
        items.append(item)
    return items


@router.post("/{ad_id}", status_code=status.HTTP_204_NO_CONTENT)
async def add_favorite(ad_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    ad_result = await db.execute(select(Ad.id).where(Ad.id == ad_id))
    if ad_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Объявление не найдено")

    existing = await db.execute(
        select(Favorite).where(Favorite.user_id == user.id, Favorite.ad_id == ad_id)
    )
    if existing.scalar_one_or_none() is not None:
        return  # уже в избранном — идемпотентно

    db.add(Favorite(user_id=user.id, ad_id=ad_id))
    await db.commit()


@router.delete("/{ad_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_favorite(ad_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Favorite).where(Favorite.user_id == user.id, Favorite.ad_id == ad_id))
    favorite = result.scalar_one_or_none()
    if favorite is not None:
        await db.delete(favorite)
        await db.commit()
