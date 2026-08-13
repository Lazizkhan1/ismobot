from sqlalchemy import func, select, update

from database.models import Category
from database.session import async_session
from database.utils import to_dict, to_dicts


class CategoriesService:
    async def getAll(self):
        async with async_session() as session:
            result = await session.scalars(
                select(Category).where(Category.deleted_at.is_(None)).order_by(Category.id)
            )
            return to_dicts(result.all())

    async def getById(self, id):
        async with async_session() as session:
            result = await session.scalar(
                select(Category).where(Category.id == id, Category.deleted_at.is_(None))
            )
            return to_dict(result)

    async def create(self, name):
        async with async_session() as session:
            category = Category(name=name)
            session.add(category)
            await session.commit()
            await session.refresh(category)
            return to_dict(category)

    async def delete(self, id):
        async with async_session() as session:
            result = await session.execute(
                update(Category)
                .where(Category.id == id)
                .values(deleted_at=func.now())
                .returning(Category.id)
            )
            row = result.fetchone()
            await session.commit()
            return {"id": row[0]} if row else None
