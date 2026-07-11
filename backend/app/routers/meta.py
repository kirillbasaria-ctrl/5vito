from fastapi import APIRouter

from app.constants import CATEGORY_LABELS, CITY_LABELS
from app.schemas import MetaOut

router = APIRouter(prefix="/api/meta", tags=["meta"])


@router.get("", response_model=MetaOut)
async def get_meta():
    return MetaOut(
        categories=[{"slug": slug, "label": label} for slug, label in CATEGORY_LABELS.items()],
        cities=[{"slug": slug, "label": label} for slug, label in CITY_LABELS.items()],
    )
