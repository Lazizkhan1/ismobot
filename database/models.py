from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    PrimaryKeyConstraint,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str | None] = mapped_column(String(255))
    lang: Mapped[str | None] = mapped_column(String(3))
    user_type: Mapped[int | None] = mapped_column(Integer)
    full_name: Mapped[str | None] = mapped_column(String(255), default=None)
    channel_message_id: Mapped[int | None] = mapped_column(BigInteger, default=None)
    group_message_id: Mapped[int | None] = mapped_column(BigInteger, default=None)
    referrer_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"), default=None)

    orders: Mapped[list["Order"]] = relationship(back_populates="user")
    referrals_given: Mapped[list["Referral"]] = relationship(
        "Referral", back_populates="referrer", foreign_keys="[Referral.referrer_id]"
    )


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
    discount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("30000"))
    created_at: Mapped[datetime | None] = mapped_column(DateTime, server_default=func.current_date())

    user: Mapped[User | None] = relationship(back_populates="orders")
    category: Mapped[Category | None] = relationship(back_populates="orders")
    photos: Mapped[list["OrderPhoto"]] = relationship(back_populates="order")
    order_messages: Mapped[list["OrderMessage"]] = relationship(back_populates="order")


class OrderPhoto(Base):
    __tablename__ = "order_photos"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    order_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("orders.id"))
    photo_id: Mapped[str | None] = mapped_column(String)

    order: Mapped[Order | None] = relationship(back_populates="photos")


class OrderMessage(Base):
    __tablename__ = "order_messages"
    __table_args__ = (PrimaryKeyConstraint("chat_id", "message_id"),)

    chat_id: Mapped[int] = mapped_column(BigInteger)
    message_id: Mapped[int] = mapped_column(BigInteger)
    order_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("orders.id"))
    content: Mapped[str] = mapped_column(String)

    order: Mapped[Order | None] = relationship(back_populates="order_messages")


class Discount(Base):
    __tablename__ = "discounts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, default=None)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    is_percentage: Mapped[bool] = mapped_column(Boolean, default=False)
    discrete: Mapped[bool] = mapped_column(Boolean, default=False)
    referral_milestone: Mapped[int | None] = mapped_column(Integer, default=None)
    is_overflow: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Referral(Base):
    __tablename__ = "referrals"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    referrer_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    new_customer_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    referrer: Mapped["User"] = relationship(
        "User", back_populates="referrals_given", foreign_keys=[referrer_id]
    )
    new_customer: Mapped["User"] = relationship("User", foreign_keys=[new_customer_id])


class DiscountHistory(Base):
    __tablename__ = "discount_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    discount_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("discounts.id"), default=None)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    is_percentage: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(20), default="active")  # 'active', 'consumed', 'superseded'
    superseded_by: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("discount_history.id"), default=None
    )
    order_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("orders.id"), default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class OrderDiscount(Base):
    __tablename__ = "order_discount"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("orders.id"))
    discount_history_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("discount_history.id"), default=None
    )
    applied_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    is_percentage: Mapped[bool] = mapped_column(Boolean, default=False)