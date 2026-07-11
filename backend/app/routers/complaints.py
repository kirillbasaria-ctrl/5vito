from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models import Ad, Complaint, User
from app.schemas import ComplaintCreateIn, ComplaintOut

router = APIRouter(prefix="/api/complaints", tags=["complaints"])


@router.post("", response_model=ComplaintOut, status_code=status.HTTP_201_CREATED)
async def create_complaint(
    data: ComplaintCreateIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    ad_result = await db.execute(select(Ad.id).where(Ad.id == data.ad_id))
    if ad_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Объявление не найдено")

    complaint = Complaint(
        author_id=user.id,
        ad_id=data.ad_id,
        reason=data.reason.value,
        text=(data.text or "").strip() or None,
    )
    db.add(complaint)
    await db.commit()
    await db.refresh(complaint)
    return complaint


@router.get("/mine", response_model=list[ComplaintOut])
async def list_my_complaints(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Complaint).where(Complaint.author_id == user.id).order_by(Complaint.created_at.desc())
    )
    return result.scalars().all()
