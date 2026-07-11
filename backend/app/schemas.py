"""
Pydantic V2 схемы. Разделены по сущностям: Auth, User, Ad, AdImage, Favorite,
Review, Complaint, Meta.
"""
from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.constants import CategoryEnum, CityEnum, ComplaintReasonEnum, ComplaintStatusEnum, RoleEnum

# --------------------------------------------------------------------------
# Общее
# --------------------------------------------------------------------------

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int


class MetaOut(BaseModel):
    categories: list[dict]
    cities: list[dict]


# --------------------------------------------------------------------------
# Auth / User
# --------------------------------------------------------------------------

class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    name: str = Field(min_length=1, max_length=120)

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Имя не может быть пустым")
        return v


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class RefreshIn(BaseModel):
    refresh_token: str


class TokenPairOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    name: str
    phone: str | None
    city: str | None
    role: RoleEnum
    created_at: datetime


class UserPublicOut(BaseModel):
    """Публичный профиль продавца (без email)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    city: str | None
    created_at: datetime


class UserUpdateIn(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    phone: str | None = Field(default=None, max_length=32)
    city: CityEnum | None = None


# --------------------------------------------------------------------------
# Ads
# --------------------------------------------------------------------------

class AdImageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    url: str
    position: int


class AdCreateIn(BaseModel):
    title: str = Field(min_length=3, max_length=150)
    description: str = Field(min_length=10, max_length=5000)
    price: float | None = Field(default=None, ge=0)
    category: CategoryEnum
    city: CityEnum
    is_draft: bool = False


class AdUpdateIn(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=150)
    description: str | None = Field(default=None, min_length=10, max_length=5000)
    price: float | None = Field(default=None, ge=0)
    category: CategoryEnum | None = None
    city: CityEnum | None = None


class AdPublishIn(BaseModel):
    is_draft: bool  # True -> перевести в черновик, False -> опубликовать


class AdOwnerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    phone: str | None


class AdOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    price: float | None
    category: CategoryEnum
    city: CityEnum
    status: str
    views: int
    created_at: datetime
    updated_at: datetime
    owner: AdOwnerOut
    images: list[AdImageOut] = []
    is_favorited: bool = False


class AdListItemOut(BaseModel):
    """Облегчённая карточка для списков объявлений."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    price: float | None
    category: CategoryEnum
    city: CityEnum
    status: str
    created_at: datetime
    cover_image: str | None = None


# --------------------------------------------------------------------------
# Favorites
# --------------------------------------------------------------------------

class FavoriteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ad: AdListItemOut
    created_at: datetime


# --------------------------------------------------------------------------
# Reviews
# --------------------------------------------------------------------------

class ReviewCreateIn(BaseModel):
    target_user_id: int
    ad_id: int | None = None
    rating: int = Field(ge=1, le=5)
    text: str = Field(min_length=1, max_length=2000)


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    author: UserPublicOut
    target_user_id: int
    ad_id: int | None
    rating: int
    text: str
    created_at: datetime


class SellerProfileOut(BaseModel):
    user: UserPublicOut
    average_rating: float | None
    reviews_count: int
    active_ads_count: int


# --------------------------------------------------------------------------
# Complaints
# --------------------------------------------------------------------------

class ComplaintCreateIn(BaseModel):
    ad_id: int
    reason: ComplaintReasonEnum
    text: str | None = Field(default=None, max_length=2000)


class ComplaintOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ad_id: int
    reason: ComplaintReasonEnum
    text: str | None
    status: ComplaintStatusEnum
    created_at: datetime
