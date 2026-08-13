from sqlalchemy import delete, select

from database.models import OrderPhoto
from database.session import async_session
from database.utils import to_dict, to_dicts


class OrderPhotosService:
    async def get_order_photos(self, order_id):
        async with async_session() as session:
            result = await session.scalars(
                select(OrderPhoto).where(OrderPhoto.order_id == order_id)
            )
            return to_dicts(result.all())

    async def add_order_photo(self, order_id, photo_id):
        async with async_session() as session:
            photo = OrderPhoto(order_id=order_id, photo_id=photo_id)
            session.add(photo)
            await session.commit()
            await session.refresh(photo)
            return to_dict(photo)

    async def delete_order_photo(self, order_id, photo_id):
        async with async_session() as session:
            result = await session.scalars(
                delete(OrderPhoto)
                .where(OrderPhoto.order_id == order_id, OrderPhoto.photo_id == photo_id)
                .returning(OrderPhoto)
            )
            photo = result.first()
            await session.commit()
            return to_dict(photo)
