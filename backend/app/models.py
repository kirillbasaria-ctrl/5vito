"""
Модели SQLAlchemy 2.0 (async, Mapped/mapped_column стиль).
"""
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.constants import (
    AdStatusEnum,
    CategoryEnum,
    CityEnum,
    ComplaintReasonEnum,
    ComplaintStatusEnum,
    RoleEnum,
)
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    city: Mapped[str | None] = mapped_column(SAEnum(CityEnum, native_enum=False, length=32), nullable=True)
    role: Mapped[str] = mapped_column(
        SAEnum(RoleEnum, native_enum=False, length=16), default=RoleEnum.user.value, nullable=False
    )
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    ads: Mapped[list["Ad"]] = relationship(back_populates="owner", foreign_keys="Ad.owner_id")
    favorites: Mapped[list["Favorite"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    reviews_written: Mapped[list["Review"]] = relationship(
        back_populates="author", foreign_keys="Review.author_id"
    )
    reviews_received: Mapped[list["Review"]] = relationship(
        back_populates="target_user", foreign_keys="Review.target_user_id"
    )


class Ad(Base):
    __tablename__ = "ads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    price: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)  # NULL = цена договорная
    category: Mapped[str] = mapped_column(SAEnum(CategoryEnum, native_enum=False, length=32), nullable=False)
    city: Mapped[str] = mapped_column(SAEnum(CityEnum, native_enum=False, length=32), nullable=False)
    status: Mapped[str] = mapped_column(
        SAEnum(AdStatusEnum, native_enum=False, length=16), default=AdStatusEnum.active.value, nullable=False
    )
    views: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    owner: Mapped["User"] = relationship(back_populates="ads", foreign_keys=[owner_id])
    images: Mapped[list["AdImage"]] = relationship(
        back_populates="ad", cascade="all, delete-orphan", order_by="AdImage.position"
    )
    favorited_by: Mapped[list["Favorite"]] = relationship(back_populates="ad", cascade="all, delete-orphan")
    complaints: Mapped[list["Complaint"]] = relationship(back_populates="ad", cascade="all, delete-orphan")


class AdImage(Base):
    __tablename__ = "ad_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ad_id: Mapped[int] = mapped_column(ForeignKey("ads.id", ondelete="CASCADE"), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    ad: Mapped["Ad"] = relationship(back_populates="images")


class Favorite(Base):
    __tablename__ = "favorites"
    __table_args__ = (UniqueConstraint("user_id", "ad_id", name="uq_favorite_user_ad"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    ad_id: Mapped[int] = mapped_column(ForeignKey("ads.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="favorites")
    ad: Mapped["Ad"] = relationship(back_populates="favorited_by")


class Review(Base):
    """Отзыв о продавце (пользователе), опционально привязан к объявлению."""

    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    target_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    ad_id: Mapped[int | None] = mapped_column(ForeignKey("ads.id", ondelete="SET NULL"), nullable=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1..5
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    author: Mapped["User"] = relationship(back_populates="reviews_written", foreign_keys=[author_id])
    target_user: Mapped["User"] = relationship(back_populates="reviews_received", foreign_keys=[target_user_id])
    ad: Mapped["Ad | None"] = relationship()


class Complaint(Base):
    """Жалоба на объявление."""

    __tablename__ = "complaints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    ad_id: Mapped[int] = mapped_column(ForeignKey("ads.id", ondelete="CASCADE"), nullable=False)
    reason: Mapped[str] = mapped_column(
        SAEnum(ComplaintReasonEnum, native_enum=False, length=32), nullable=False
    )
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        SAEnum(ComplaintStatusEnum, native_enum=False, length=16),
        default=ComplaintStatusEnum.new.value,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    author: Mapped["User"] = relationship(foreign_keys=[author_id])
    ad: Mapped["Ad"] = relationship(back_populates="complaints")
