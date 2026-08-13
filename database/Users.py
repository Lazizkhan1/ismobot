from sqlalchemy import select, update

from database.models import User
from database.session import async_session
from database.utils import to_dict, to_dicts


class UsersService:
    async def getAll(self):
        async with async_session() as session:
            result = await session.scalars(select(User))
            return to_dicts(result.all())

    async def getAllUsersByType(self, user_type_id):
        return await self.getAllByUserType(user_type_id)

    async def getById(self, user_id: int) -> dict | None:
        async with async_session() as session:
            user = await session.get(User, user_id)
            return to_dict(user)

    async def getLanguageById(self, user_id):
        async with async_session() as session:
            result = await session.execute(select(User.lang).where(User.id == user_id))
            row = result.fetchone()
            return {"lang": row[0]} if row else None

    async def create(self, id: int, username: str, lang: str, typeId: int):
        async with async_session() as session:
            user = User(id=id, username=username, lang=lang, user_type=typeId)
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return to_dict(user)

    async def updateUserType(self, user_id, type_id):
        async with async_session() as session:
            await session.execute(
                update(User).where(User.id == user_id).values(user_type=type_id)
            )
            await session.commit()

    async def getAllByUserType(self, user_type):
        async with async_session() as session:
            result = await session.scalars(select(User).where(User.user_type == user_type))
            return to_dicts(result.all())

    async def setLanguage(self, user_id, lang):
        async with async_session() as session:
            await session.execute(update(User).where(User.id == user_id).values(lang=lang))
            await session.commit()
