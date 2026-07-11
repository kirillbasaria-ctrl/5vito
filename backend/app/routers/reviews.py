from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.deps import get_current_user
from app.models import Review, User
from app.schemas import ReviewCreateIn, ReviewOut

router = APIRouter(prefix="/api/reviews", tags=["reviews"])


@router.get("/user/{user_id}", response_model=list[ReviewOut])
async def list_reviews_for_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Review)
        .where(Review.target_user_id == user_id)
        .options(selectinload(Review.author))
        .order_by(Review.created_at.desc())
    )
    return result.scalars().all()


@router.post("", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
async def create_review(
    data: ReviewCreateIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    if data.target_user_id == user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Нельзя оставить отзыв самому себе")

    target_result = await db.execute(select(User.id).where(User.id == data.target_user_id))
    if target_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

    review = Review(
        author_id=user.id,
        target_user_id=data.target_user_id,
        ad_id=data.ad_id,
        rating=data.rating,
        text=data.text.strip(),
    )
    db.add(review)
    await db.commit()

    result = await db.execute(
        select(Review).where(Review.id == review.id).options(selectinload(Review.author))
    )
    return result.scalar_one()


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(review_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Review).where(Review.id == review_id))
    review = result.scalar_one_or_none()
    if review is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Отзыв не найден")

    is_author = review.author_id == user.id
    is_staff = user.role in ("moderator", "admin")
    if not (is_author or is_staff):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")

    await db.delete(review)
    await db.commit()
