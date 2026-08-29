from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert

from database.models import User
from database.session import async_session
from database.utils import to_dict, to_dicts


async def getById(user_id: int) -> User | None:
    async with async_session() as session:
        user = await session.get(User, user_id)
        return user


async def update_user(user: User):
    async with async_session() as session:
        smt = (
            update(User)
            .where(User.id == user.id)
            .values(
                username=user.username,
                full_name=user.full_name,
                lang=user.lang,
                user_type=user.user_type,
            ).
            returning(User)
        )
        result = await session.execute(smt)
        updated_user = result.scalar_one()
        await session.commit()
        return updated_user


async def set_referrer(user_id: int, referrer_id: int):
    async with async_session() as session:
        await session.execute(
            update(User).where(User.id == user_id).values(referrer_id=referrer_id)
        )
        await session.commit()


class UsersService:
    async def getAll(self):
        async with async_session() as session:
            result = await session.scalars(select(User))
            return to_dicts(result.all())

    async def getAllUsersByType(self, user_type_id):
        return await self.getAllByUserType(user_type_id)

    async def getLanguageById(self, user_id):
        async with async_session() as session:
            result = await session.execute(select(User.lang).where(User.id == user_id))
            row = result.fetchone()
            return {"lang": row[0]} if row else None

    async def create(
        self,
        id: int,
        username: str | None,
        fullname: str,
        lang: str,
        typeId: int,
        referrer_id: int | None = None,
    ):
        async with async_session() as session:
            smt = (
                insert(User)
                .values(
                    id=id,
                    username=username,
                    full_name=fullname,
                    lang=lang,
                    user_type=typeId,
                    referrer_id=referrer_id,
                )
                .returning(User)
            )
            result = await session.execute(smt)
            user = result.scalar_one()
            await session.commit()
            await session.flush()
            return user

    async def create_user(self, user: User):
        async with async_session() as session:
            session.add(user)
            await session.commit()
            return await session.refresh(user)


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
