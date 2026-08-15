import datetime
import logging

from aiogram import F, Router
from aiogram.enums import ContentType, ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.formatting import Bold, Text

from bot_instance import bot
from Config import ADMIN, CARD_NUMBER, FAST_DELIVERY, SLOW_DELIVERY
from database import Orders, UserType, Users
from database.Categories import CategoriesService
from handlers.States import OrderState
from handlers.Translation import _
from handlers.keyboard import delivery_type, order_accept

router = Router()

users_service = Users.UsersService()
user_type_service = UserType.UserTypeService()
orders_service = Orders.OrdersService()
category_service = CategoriesService()


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
    await state.set_state(OrderState.delivery_type)
    await bot.send_message(
        chat_id=message.from_user.id,
        text=_(
            "Мы рады сотрудничеству с вами. \nПроцесс идентификации вашего видео осуществляется через наш бот. Как только фотографии будут обнаружены, они незамедлительно будут вам предоставлены. \n\nСтоимость услуги составляет <b>30 000 сумов</b>. В случае если ваши фотографии не будут найдены, произведенная оплата будет возвращена в полном объеме (100%).",
            lang,
        ),
        reply_markup=delivery_type(lang),
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(F.data.startswith("delivery_"))
async def order_delivery_type_select(query: CallbackQuery, state: FSMContext, lang: str) -> None:
    del_type = query.data.split("_")[-1]
    price = FAST_DELIVERY if del_type == "fast" else SLOW_DELIVERY
    await state.update_data(delivery_type=del_type, price=price)
    await state.set_state(OrderState.cheque_id)

    content = Text(
        _("Стоимость заказа: ", lang),
        Bold(f"{price:,}".replace(",", " ")),
        Text(_(" сум\n", lang)),
        _("Оплатите на карту: ", lang),
        CARD_NUMBER,
        Text("\n"),
        Bold(_("Пришлите скриншот квитанции об оплате!", lang)),
    )
    await query.message.edit_text(**content.as_kwargs())
    await query.answer(_("Доставка выбрана!", lang))


@router.message(OrderState.cheque_id)
async def order_cheque_id(message: Message, state: FSMContext, lang: str) -> None:
    if message.content_type != ContentType.PHOTO:
        await message.answer(_("Пришлите скриншот квитанции об оплате!", lang))
        return

    cheque_id = message.photo[-1].file_id
    data = await state.get_data()
    logging.info(data)
    order = await orders_service.create(
        message.from_user.id,
        data["category_id"],
        data["ceremony_date"],
        data["video_note_id"],
        cheque_id,
    )

    category = await category_service.getById(data["category_id"])
    cat_name = category["name"] if category else str(data["category_id"])
    del_speed = (
        _("Быстрая (2 часа)", lang)
        if data.get("delivery_type") == "fast"
        else _("Обычная (24 часа)", lang)
    )

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
                f"{_('Доставка: ', lang)}{del_speed}",
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

