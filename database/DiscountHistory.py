from decimal import Decimal
from sqlalchemy import select, update

from Config import OVERFLOW_DISCOUNT_AMOUNT
from database.Discounts import DiscountsService
from database.models import DiscountHistory
from database.session import async_session
from database.utils import to_dict, to_dicts

discounts_service = DiscountsService()


class DiscountHistoryService:
    async def get_by_id(self, discount_history_id: int) -> DiscountHistory | None:
        async with async_session() as session:
            return await session.get(DiscountHistory, discount_history_id)

    async def earn_milestone(self, user_id: int, referral_count: int) -> DiscountHistory | None:
        discount = await discounts_service.get_by_milestone(referral_count)
        if not discount:
            return None

        async with async_session() as session:
            existing_pct_result = await session.scalars(
                select(DiscountHistory).where(
                    DiscountHistory.user_id == user_id,
                    DiscountHistory.is_percentage.is_(True),
                    DiscountHistory.status == "active",
                )
            )
            existing_pct = existing_pct_result.all()

            new_entry = DiscountHistory(
                user_id=user_id,
                discount_id=discount.id,
                amount=discount.discount_amount,
                is_percentage=True,
                status="active",
            )
            session.add(new_entry)
            await session.flush()

            for old in existing_pct:
                old.status = "superseded"
                old.superseded_by = new_entry.id

            await session.commit()
            await session.refresh(new_entry)
            return new_entry

    async def earn_overflow(self, user_id: int) -> DiscountHistory:
        overflow_discount = await discounts_service.get_overflow()
        async with async_session() as session:
            entry = DiscountHistory(
                user_id=user_id,
                discount_id=overflow_discount.id if overflow_discount else None,
                amount=Decimal(str(OVERFLOW_DISCOUNT_AMOUNT)),
                is_percentage=False,
                status="active",
            )
            session.add(entry)
            await session.commit()
            await session.refresh(entry)
            return entry

    async def get_available_summary(self, user_id: int) -> dict:
        async with async_session() as session:
            active_result = await session.scalars(
                select(DiscountHistory)
                .where(
                    DiscountHistory.user_id == user_id,
                    DiscountHistory.status == "active",
                )
                .order_by(DiscountHistory.amount.desc())
            )
            rows = active_result.all()

        pct_entries = [r for r in rows if r.is_percentage]
        dis_entries = [r for r in rows if not r.is_percentage]

        result = {"percentage": None, "discrete": None}

        if pct_entries:
            best = max(pct_entries, key=lambda r: r.amount)
            result["percentage"] = {
                "id": best.id,
                "amount": best.amount,
                "label": f"{int(best.amount)}% off",
            }

        if dis_entries:
            total = sum(r.amount for r in dis_entries)
            result["discrete"] = {
                "ids": [r.id for r in dis_entries],
                "total": total,
                "label": f"{int(total):,} so'm".replace(",", " "),
            }

        return result

    async def consume(self, user_id: int, history_ids: list[int], order_id: int) -> None:
        if not history_ids:
            return
        async with async_session() as session:
            await session.execute(
                update(DiscountHistory)
                .where(
                    DiscountHistory.id.in_(history_ids),
                    DiscountHistory.user_id == user_id,
                )
                .values(status="consumed", order_id=order_id)
            )
            await session.commit()

    async def get_history_by_user(self, user_id: int):
        async with async_session() as session:
            result = await session.scalars(
                select(DiscountHistory)
                .where(DiscountHistory.user_id == user_id)
                .order_by(DiscountHistory.created_at.desc())
            )
            return to_dicts(result.all())
