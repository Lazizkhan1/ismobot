from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from aiogram.utils.deep_linking import create_start_link

from bot_instance import bot
from Config import ORDER_PRICE
from database.DiscountHistory import DiscountHistoryService
from database.Orders import OrdersService
from database.Referrals import ReferralsService
from database.Users import UsersService
from handlers.keyboard import (
    all_categories,
    discount_picker_keyboard,
    invite_friends_menu_keyboard,
    main_menu_keyboard,
)
from handlers.States import OrderState
from handlers.Translation import _

router = Router()
referrals_service = ReferralsService()
discount_history_service = DiscountHistoryService()
orders_service = OrdersService()
users_service = UsersService()


@router.callback_query(F.data == "referral_menu")
async def show_referral_menu(query: CallbackQuery, lang: str) -> None:
    await query.answer()
    await query.message.answer(
        _("👥 Меню приглашений:", lang),
        reply_markup=invite_friends_menu_keyboard(lang),
    )


@router.callback_query(F.data == "referral_invite")
async def send_invite_link(query: CallbackQuery, lang: str) -> None:
    await query.answer()
    link = await create_start_link(bot, str(query.from_user.id), encode=True)
    text = _(
        "🔗 Ваша реферальная ссылка:\n{link}\n\n🎁 Поделитесь с друзьями и получите скидку до 100%!",
        lang,
    ).format(link=link)
    await query.message.answer(text)


@router.callback_query(F.data == "referral_discounts")
async def show_my_discounts(query: CallbackQuery, lang: str) -> None:
    await query.answer()
    count = await referrals_service.get_count(query.from_user.id)
    summary = await discount_history_service.get_available_summary(query.from_user.id)

    if count == 0 and not summary.get("percentage") and not summary.get("discrete"):
        text = _(
            "😔 Пока нет приглашённых друзей.\nПоделитесь ссылкой и получайте скидки!",
            lang,
        )
    else:
        discounts_list = []
        if summary.get("percentage"):
            discounts_list.append(f"• 🎁 {summary['percentage']['label']}")
        if summary.get("discrete"):
            discounts_list.append(f"• 💵 {summary['discrete']['label']}")
        if not discounts_list:
            discounts_list.append("• 0")

        discounts_str = "\n".join(discounts_list)
        text = _(
            "🎉 Вы пригласили {count} друзей!\n\n🎁 Доступные скидки:\n{discounts}",
            lang,
        ).format(count=count, discounts=discounts_str)

    await query.message.answer(text, reply_markup=invite_friends_menu_keyboard(lang))


@router.callback_query(F.data == "main_menu")
async def go_to_main_menu(query: CallbackQuery, state: FSMContext, lang: str) -> None:
    await query.answer()
    await state.clear()
    await query.message.answer(
        _("👋 Привет! Что хотите сделать?", lang),
        reply_markup=main_menu_keyboard(lang),
    )


@router.callback_query(F.data == "order_photo")
async def start_order(query: CallbackQuery, state: FSMContext, lang: str) -> None:
    await query.answer()
    await state.clear()
    await query.message.answer(
        _("📸 Выберите категорию:", lang),
        reply_markup=await all_categories("order_"),
    )


@router.callback_query(F.data == "contact_admin")
async def contact_admin_cb(query: CallbackQuery, lang: str) -> None:
    await query.answer()
    await query.message.answer(
        _("Если у вас возникнут какие-либо проблемы с ботом, пожалуйста, свяжитесь с @ismo_group_admin !", lang)
    )


@router.callback_query(F.data == "use_earned_discount")
async def use_earned_discount(query: CallbackQuery, state: FSMContext, lang: str) -> None:
    await query.answer()
    pending = await orders_service.get_pending_by_user(query.from_user.id)

    if pending:
        summary = await discount_history_service.get_available_summary(query.from_user.id)
        has_any = summary.get("percentage") is not None or summary.get("discrete") is not None
        if has_any:
            await state.set_state(OrderState.select_discount)
            await state.update_data(
                category_id=pending["category_id"],
                ceremony_date=str(pending["ceremony_date"]),
                video_note_id=pending["video_note_id"],
                discount_summary=summary,
            )
            price_str = f"{ORDER_PRICE:,}".replace(",", " ")
            await query.message.answer(
                _(
                    "🎉 У вас есть скидка!\n💳 Стоимость заказа: <b>{price} сум</b>\n\nКакую скидку вы хотите использовать?",
                    lang,
                ).format(price=price_str),
                reply_markup=discount_picker_keyboard(summary, lang),
                parse_mode=ParseMode.HTML,
            )
            return

    await query.message.answer(
        _("🏠 Ваша скидка сохранена!\nПерейдите в главное меню, чтобы оформить заказ.", lang),
        reply_markup=main_menu_keyboard(lang),
    )

