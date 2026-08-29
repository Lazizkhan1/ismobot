from decimal import Decimal
from sqlalchemy import select

from database.models import OrderDiscount
from database.session import async_session
from database.utils import to_dict


class OrderDiscountService:
    async def create(
        self,
        order_id: int,
        applied_amount: Decimal | int | float,
        is_percentage: bool = False,
        discount_history_id: int | None = None,
    ) -> OrderDiscount:
        async with async_session() as session:
            od = OrderDiscount(
                order_id=order_id,
                applied_amount=Decimal(str(applied_amount)),
                is_percentage=is_percentage,
                discount_history_id=discount_history_id,
            )
            session.add(od)
            await session.commit()
            await session.refresh(od)
            return od

    async def get_by_order(self, order_id: int):
        async with async_session() as session:
            result = await session.scalars(
                select(OrderDiscount).where(OrderDiscount.order_id == order_id).limit(1)
            )
            return to_dict(result.first())
