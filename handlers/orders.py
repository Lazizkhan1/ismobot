import datetime
import logging

from aiogram import F, Router
from aiogram.enums import ContentType, ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.formatting import Bold, Text

from bot_instance import bot
from Config import ADMIN, CARD_NUMBER, ORDER_PRICE
from database import Orders, UserType, Users
from database.Categories import CategoriesService
from database.DiscountHistory import DiscountHistoryService
from database.OrderDiscount import OrderDiscountService
from handlers.States import OrderState
from handlers.Translation import _
from handlers.keyboard import (
    discount_picker_keyboard,
    order_accept,
    pay_now_keyboard,
)

router = Router()

users_service = Users.UsersService()
user_type_service = UserType.UserTypeService()
orders_service = Orders.OrdersService()
category_service = CategoriesService()
discount_history_service = DiscountHistoryService()
order_discount_service = OrderDiscountService()


@router.callback_query(F.data.startswith("order_category:"))
async def order_category_select(query: CallbackQuery, state: FSMContext, lang: str) -> None:
    category_id = int(query.data.split(":")[-1])
    await state.update_data(category_id=category_id)

    await state.set_state(OrderState.ceremony_date)
    await query.message.edit_text(
        _("Введите дату церемонии! \nНапример: <b>(24.10.2024)</b>", lang),
        parse_mode=ParseMode.HTML,
    )
    await query.answer(_("Категория выбрана!", lang))


@router.message(OrderState.ceremony_date)
async def order_ceremony_date(message: Message, state: FSMContext, lang: str) -> None:
    date_str = message.text.strip().split(".")
    if len(date_str) != 3:
        await message.answer(
            _("Неверный формат даты!", lang)
            + "\n"
            + _("Введите дату церемонии! \nНапример: <b>(24.10.2024)</b>", lang),
            parse_mode=ParseMode.HTML,
        )
        return

    try:
        if len(date_str[2]) == 2:
            date_str[2] = "20" + date_str[2]
        date = datetime.date(int(date_str[2]), int(date_str[1]), int(date_str[0]))
        await state.update_data(ceremony_date=date.strftime("%Y-%m-%d"))
        await state.set_state(OrderState.video_note_id)
        await message.answer(
            _(
                "Пожалуйста, отправьте видеокружок (круглое видео) с вашим лицом не менее <b>3 секунд</b>! \nНам нужно это видео, чтобы мы могли узнать вас по фотографии!",
                lang,
            ),
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        await message.answer(
            _("Неверный формат даты!", lang)
            + "\n"
            + _("Введите дату церемонии! \nНапример: <b>(24.10.2024)</b>", lang),
            parse_mode=ParseMode.HTML,
        )


@router.message(OrderState.video_note_id)
async def order_video_note(message: Message, state: FSMContext, lang: str) -> None:
    if message.content_type != ContentType.VIDEO_NOTE or message.video_note.duration < 3:
        await message.answer(
            _(
                "Пожалуйста, отправьте видеокружок (круглое видео) с вашим лицом не менее <b>3 секунд</b>! \nНам нужно это видео, чтобы мы могли узнать вас по фотографии!",
                lang,
            ),
            parse_mode=ParseMode.HTML,
        )
        return

    video_note_id = message.video_note.file_id
    await state.update_data(video_note_id=video_note_id)

    # Check available discounts
    summary = await discount_history_service.get_available_summary(message.from_user.id)
    has_any = summary.get("percentage") is not None or summary.get("discrete") is not None

    price_str = f"{ORDER_PRICE:,}".replace(",", " ")

    if has_any:
        await state.set_state(OrderState.select_discount)
        await state.update_data(discount_summary=summary)
        await bot.send_message(
            chat_id=message.from_user.id,
            text=_(
                "🎉 У вас есть скидка!\n💳 Стоимость заказа: <b>{price} сум</b>\n\nКакую скидку вы хотите использовать?",
                lang,
            ).format(price=price_str),
            reply_markup=discount_picker_keyboard(summary, lang),
            parse_mode=ParseMode.HTML,
        )
    else:
        await state.set_state(OrderState.cheque_id)
        await state.update_data(discount=0, total_amount=ORDER_PRICE, applied_history_ids=[])
        await bot.send_message(
            chat_id=message.from_user.id,
            text=_(
                "💳 Стоимость заказа: <b>{price} сум</b>\n📲 Оплатите на карту: <b>{card}</b>\n\n✅ После оплаты отправьте скриншот чека!",
                lang,
            ).format(price=price_str, card=CARD_NUMBER),
            parse_mode=ParseMode.HTML,
        )


@router.callback_query(F.data.startswith("apply_discount:pct:"), OrderState.select_discount)
async def apply_pct_discount(query: CallbackQuery, state: FSMContext, lang: str) -> None:
    await query.answer()
    history_id = int(query.data.split(":")[2])
    data = await state.get_data()
    summary = data.get("discount_summary", {})
    pct_info = summary.get("percentage", {})
    pct = pct_info.get("amount", 0)

    discount_value = int(ORDER_PRICE * pct / 100)
    total_amount = max(0, ORDER_PRICE - discount_value)

    await state.update_data(
        discount=discount_value,
        total_amount=total_amount,
        applied_history_ids=[history_id],
        is_percentage=True,
    )
    await state.set_state(OrderState.cheque_id)

    label = f"-{int(pct)}%"
    await query.message.answer(
        _(
            "✅ Скидка применена: {label}\n💰 Сумма к оплате: <b>{total} сум</b>\n📲 Оплатите на карту: <b>{card}</b>",
            lang,
        ).format(
            label=label,
            total=f"{total_amount:,}".replace(",", " "),
            card=CARD_NUMBER,
        ),
        reply_markup=pay_now_keyboard(total_amount, lang),
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(F.data.startswith("apply_discount:dis:"), OrderState.select_discount)
async def apply_dis_discount(query: CallbackQuery, state: FSMContext, lang: str) -> None:
    await query.answer()
    ids_str = query.data.split(":")[2]
    history_ids = [int(i) for i in ids_str.split(",") if i]
    data = await state.get_data()
    summary = data.get("discount_summary", {})
    dis_info = summary.get("discrete", {})
    total_discrete = int(dis_info.get("total", 0))

    discount_value = min(total_discrete, ORDER_PRICE)
    total_amount = max(0, ORDER_PRICE - discount_value)

    await state.update_data(
        discount=discount_value,
        total_amount=total_amount,
        applied_history_ids=history_ids,
        is_percentage=False,
    )
    await state.set_state(OrderState.cheque_id)

    label = f"-{total_discrete:,} so'm".replace(",", " ")
    await query.message.answer(
        _(
            "✅ Скидка применена: {label}\n💰 Сумма к оплате: <b>{total} сум</b>\n📲 Оплатите на карту: <b>{card}</b>",
            lang,
        ).format(
            label=label,
            total=f"{total_amount:,}".replace(",", " "),
            card=CARD_NUMBER,
        ),
        reply_markup=pay_now_keyboard(total_amount, lang),
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(F.data == "skip_discount", OrderState.select_discount)
async def skip_discount(query: CallbackQuery, state: FSMContext, lang: str) -> None:
    await query.answer()
    await state.update_data(discount=0, total_amount=ORDER_PRICE, applied_history_ids=[])
    await state.set_state(OrderState.cheque_id)
    price_str = f"{ORDER_PRICE:,}".replace(",", " ")
    await query.message.answer(
        _(
            "💳 Стоимость заказа: <b>{price} сум</b>\n📲 Оплатите на карту: <b>{card}</b>\n\n✅ После оплаты отправьте скриншот чека!",
            lang,
        ).format(price=price_str, card=CARD_NUMBER),
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(F.data == "confirm_pay")
async def confirm_pay(query: CallbackQuery, state: FSMContext, lang: str) -> None:
    await query.answer()
    await query.message.answer(_("📸 Отправьте скриншот оплаты!", lang))


@router.message(OrderState.cheque_id)
async def order_cheque_id(message: Message, state: FSMContext, lang: str) -> None:
    if message.content_type != ContentType.PHOTO:
        await message.answer(_("📸 Отправьте скриншот оплаты!", lang))
        return

    cheque_id = message.photo[-1].file_id
    data = await state.get_data()
    logging.info(data)

    discount = data.get("discount", 0)
    total_amount = data.get("total_amount", ORDER_PRICE)
    applied_history_ids = data.get("applied_history_ids", [])
    is_percentage = data.get("is_percentage", False)

    order = await orders_service.create(
        message.from_user.id,
        data["category_id"],
        data["ceremony_date"],
        data["video_note_id"],
        cheque_id,
        discount=discount,
        total_amount=total_amount,
    )

    if applied_history_ids:
        await order_discount_service.create(
            order_id=order["id"],
            applied_amount=discount,
            is_percentage=is_percentage,
            discount_history_id=applied_history_ids[0] if len(applied_history_ids) == 1 else None,
        )
        await discount_history_service.consume(
            user_id=message.from_user.id,
            history_ids=applied_history_ids,
            order_id=order["id"],
        )

    category = await category_service.getById(data["category_id"])
    cat_name = category["name"] if category else str(data["category_id"])

    admins = await users_service.getAllByUserType(user_type_service.getAdminType())
    admin_ids = {ADMIN}
    for admin in admins:
        admin_ids.add(admin["id"])

    for admin_id in admin_ids:
        try:
            await bot.send_video_note(chat_id=admin_id, video_note=data["video_note_id"])
            await bot.send_photo(
                chat_id=admin_id,
                photo=cheque_id,
                caption=f"{_('Новый заказ!\nID: ', lang)}{message.from_user.id}\n"
                f"Order ID: {order['id']}\n"
                f"{_('Категория: ', lang)}{cat_name}\n"
                f"{_('Дата: ', lang)}{data['ceremony_date']}\n"
                f"Сумма: {total_amount:,} сум (Скидка: {discount:,} сум)\n"
                f"{_('Username: ', lang)}{message.from_user.username if message.from_user.username else message.from_user.full_name}\n",
                reply_markup=order_accept(order["id"], lang),
            )
        except Exception as e:
            logging.exception("Error notifying admin %s: %s", admin_id, e)

    await state.clear()
    await message.answer(
        _("Заказ успешно оформлен! Наши администраторы отправят вам ваши фотографии как можно скорее.", lang)
    )


@router.callback_query(F.data == "flow1_pay")
async def handle_flow1_pay(query: CallbackQuery, state: FSMContext, lang: str) -> None:
    from handlers.keyboard import all_categories
    await query.answer()
    await query.message.answer(
        Bold(_("Чтобы начать заказ, вы можете начать с выбора категории ниже.", lang)).as_html(),
        reply_markup=await all_categories("order_"),
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(F.data == "flow2_continue")
async def handle_flow2_continue(query: CallbackQuery, state: FSMContext, lang: str) -> None:
    from handlers.keyboard import all_categories
    await query.answer()
    await query.message.answer(
        Bold(_("Чтобы начать заказ, вы можете начать с выбора категории ниже.", lang)).as_html(),
        reply_markup=await all_categories("order_"),
        parse_mode=ParseMode.HTML,
    )

