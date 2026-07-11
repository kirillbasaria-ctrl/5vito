from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import AdStatusEnum
from app.database import get_db
from app.deps import get_current_user
from app.models import Ad, Review, User
from app.schemas import SellerProfileOut, UserOut, UserPublicOut, UserUpdateIn

router = APIRouter(prefix="/api/users", tags=["users"])


@router.patch("/me", response_model=UserOut)
async def update_me(
    data: UserUpdateIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Используем model_fields_set, чтобы отличить "поле не передали" от
    # "поле явно очистили значением null" (актуально для phone/city).
    provided = data.model_fields_set

    if "name" in provided and data.name is not None:
        user.name = data.name
    if "phone" in provided:
        user.phone = data.phone
    if "city" in provided:
        user.city = data.city.value if data.city is not None else None

    await db.commit()
    await db.refresh(user)
    return user


@router.get("/{user_id}", response_model=SellerProfileOut)
async def get_seller_profile(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    target = result.scalar_one_or_none()
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

    rating_result = await db.execute(
        select(func.avg(Review.rating), func.count(Review.id)).where(Review.target_user_id == user_id)
    )
    avg_rating, reviews_count = rating_result.one()

    ads_count_result = await db.execute(
        select(func.count(Ad.id)).where(Ad.owner_id == user_id, Ad.status == AdStatusEnum.active.value)
    )
    active_ads_count = ads_count_result.scalar_one()

    return SellerProfileOut(
        user=UserPublicOut.model_validate(target),
        average_rating=round(float(avg_rating), 2) if avg_rating is not None else None,
        reviews_count=reviews_count or 0,
        active_ads_count=active_ads_count or 0,
    )
