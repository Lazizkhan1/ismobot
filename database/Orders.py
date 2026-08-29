from sqlalchemy import func, select, update

from database.models import Order
from database.session import async_session
from database.utils import to_dict, to_dicts
from datetime import datetime

class OrderStatus:
    PENDING = 0
    ACCEPTED = 1
    PAID = 2
    COMPLETED = 3
    CANCELED = -1


class OrdersService:
    async def getAll(self):
        async with async_session() as session:
            result = await session.scalars(select(Order).order_by(Order.id.desc()))
            return to_dicts(result.all())

    async def getById(self, id):
        async with async_session() as session:
            order = await session.get(Order, id)
            return to_dict(order)

    async def getByStatus(self, status):
        async with async_session() as session:
            result = await session.scalars(
                select(Order).where(Order.status == status).order_by(Order.id.desc())
            )
            return to_dicts(result.all())

    async def getByCategoryId(self, category_id):
        async with async_session() as session:
            result = await session.scalars(
                select(Order).where(Order.category_id == category_id).order_by(Order.id.desc())
            )
            return to_dicts(result.all())

    async def get_pending_by_user(self, user_id: int):
        async with async_session() as session:
            result = await session.scalars(
                select(Order)
                .where(
                    Order.user_id == user_id,
                    Order.status == OrderStatus.PENDING,
                    Order.video_note_id.isnot(None),
                    Order.category_id.isnot(None),
                    Order.ceremony_date.isnot(None),
                )
                .order_by(Order.id.desc())
                .limit(1)
            )
            order = result.first()
            return to_dict(order) if order else None

    async def create(
        self,
        user_id,
        category_id,
        ceremony_date,
        video_note_id,
        cheque_id,
        discount=0,
        total_amount=None,
    ):
        from decimal import Decimal
        from Config import ORDER_PRICE

        if total_amount is None:
            total_amount = max(0, ORDER_PRICE - discount)

        clean_ceremony_date = datetime.strptime(ceremony_date, "%Y-%m-%d").date()
        async with async_session() as session:
            order = Order(
                user_id=user_id,
                category_id=category_id,
                ceremony_date=clean_ceremony_date,
                video_note_id=video_note_id,
                cheque_id=cheque_id,
                discount=Decimal(str(discount)),
                total_amount=Decimal(str(total_amount)),
            )
            session.add(order)
            await session.commit()
            await session.refresh(order)
            return to_dict(order)

    async def acceptOrder(self, order_id):
        return await self._set_status(order_id, OrderStatus.ACCEPTED)

    async def completeOrder(self, order_id):
        return await self._set_status(order_id, OrderStatus.COMPLETED)

    async def cancelOrder(self, order_id, reason):
        async with async_session() as session:
            result = await session.scalars(
                update(Order)
                .where(Order.id == order_id)
                .values(
                    status=OrderStatus.CANCELED,
                    cancel_reason=reason,
                    canceled_at=func.now(),
                )
                .returning(Order)
            )
            order = result.first()
            await session.commit()
            return to_dict(order)

    async def _set_status(self, order_id, status):
        async with async_session() as session:
            result = await session.scalars(
                update(Order).where(Order.id == order_id).values(status=status).returning(Order)
            )
            order = result.first()
            await session.commit()
            return to_dict(order)
