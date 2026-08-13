from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str | None] = mapped_column(String(255))
    lang: Mapped[str | None] = mapped_column(String(3))
    user_type: Mapped[int | None] = mapped_column(Integer)

    orders: Mapped[list["Order"]] = relationship(back_populates="user")


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str | None] = mapped_column(String(255))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)

    orders: Mapped[list["Order"]] = relationship(back_populates="category")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))
    moderator_id: Mapped[int | None] = mapped_column(BigInteger, default=None)
    category_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("categories.id"))
    ceremony_date: Mapped[date | None] = mapped_column(Date)
    video_note_id: Mapped[str | None] = mapped_column(String(255))
    cheque_id: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[int | None] = mapped_column(Integer, default=0)
    cancel_reason: Mapped[str | None] = mapped_column(String(255), default=None)
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, server_default=func.current_date())

    user: Mapped[User | None] = relationship(back_populates="orders")
    category: Mapped[Category | None] = relationship(back_populates="orders")
    photos: Mapped[list["OrderPhoto"]] = relationship(back_populates="order")


class OrderPhoto(Base):
    __tablename__ = "order_photos"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    order_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("orders.id"))
    photo_id: Mapped[str | None] = mapped_column(String)

    order: Mapped[Order | None] = relationship(back_populates="photos")
