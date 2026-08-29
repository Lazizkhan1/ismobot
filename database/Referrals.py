from sqlalchemy import func, select

from database.models import Referral
from database.session import async_session
from database.utils import to_dict, to_dicts


class ReferralsService:
    async def create(self, referrer_id: int, new_customer_id: int) -> Referral:
        async with async_session() as session:
            ref = Referral(referrer_id=referrer_id, new_customer_id=new_customer_id)
            session.add(ref)
            await session.commit()
            await session.refresh(ref)
            return ref

    async def get_count(self, referrer_id: int) -> int:
        async with async_session() as session:
            result = await session.scalar(
                select(func.count()).select_from(Referral).where(Referral.referrer_id == referrer_id)
            )
            return result or 0

    async def exists(self, new_customer_id: int) -> bool:
        async with async_session() as session:
            result = await session.execute(
                select(Referral.id).where(Referral.new_customer_id == new_customer_id)
            )
            return result.first() is not None

    async def get_by_referrer(self, referrer_id: int):
        async with async_session() as session:
            result = await session.scalars(
                select(Referral).where(Referral.referrer_id == referrer_id).order_by(Referral.created_at.desc())
            )
            return to_dicts(result.all())
