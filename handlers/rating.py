from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from handlers.Translation import _

router = Router()


@router.callback_query(F.data.startswith("rate:"))
async def rate_service(query: CallbackQuery, state: FSMContext, lang: str) -> None:
    int(query.data.split(":")[-1])
    await query.message.edit_text(_("Спасибо за вашу оценку!", lang))
