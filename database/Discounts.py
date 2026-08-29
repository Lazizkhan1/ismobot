from decimal import Decimal
from sqlalchemy import func, select

from database.models import Discount
from database.session import async_session
from database.utils import to_dict, to_dicts


class DiscountsService:
    async def get_by_milestone(self, milestone: int) -> Discount | None:
        async with async_session() as session:
            result = await session.scalars(
                select(Discount)
                .where(Discount.referral_milestone == milestone)
                .order_by(Discount.discount_amount.desc())
                .limit(1)
            )
            return result.first()

    async def get_overflow(self) -> Discount | None:
        async with async_session() as session:
            result = await session.scalars(
                select(Discount)
                .where(Discount.is_overflow.is_(True))
                .order_by(Discount.id.desc())
                .limit(1)
            )
            return result.first()

    async def get_by_id(self, discount_id: int) -> Discount | None:
        async with async_session() as session:
            return await session.get(Discount, discount_id)

    async def get_all(self):
        async with async_session() as session:
            result = await session.scalars(select(Discount).order_by(Discount.id.asc()))
            return to_dicts(result.all())

    async def seed_defaults(self):
        async with async_session() as session:
            count = await session.scalar(select(func.count()).select_from(Discount))
            if count == 0:
                defaults = [
                    Discount(
                        title="1 ta do'st — 20%",
                        description="1 ta do'stni taklif qiling va 20% chegirmaga ega bo'ling",
                        discount_amount=Decimal("20.00"),
                        is_percentage=True,
                        discrete=False,
                        referral_milestone=1,
                        is_overflow=False,
                    ),
                    Discount(
                        title="2 ta do'st — 50%",
                        description="2 ta do'stni taklif qiling va 50% chegirmaga ega bo'ling",
                        discount_amount=Decimal("50.00"),
                        is_percentage=True,
                        discrete=False,
                        referral_milestone=2,
                        is_overflow=False,
                    ),
                    Discount(
                        title="3 ta do'st — 100%",
                        description="3 ta do'stni taklif qiling va 100% chegirmaga ega bo'ling",
                        discount_amount=Decimal("100.00"),
                        is_percentage=True,
                        discrete=False,
                        referral_milestone=3,
                        is_overflow=False,
                    ),
                    Discount(
                        title="Qo'shimcha taklif",
                        description="Har bir qo'shimcha do'st uchun 10 000 so'm",
                        discount_amount=Decimal("10000.00"),
                        is_percentage=False,
                        discrete=True,
                        referral_milestone=None,
                        is_overflow=True,
                    ),
                ]
                session.add_all(defaults)
                await session.commit()
