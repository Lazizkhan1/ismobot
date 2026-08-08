from asyncio.log import logger
import datetime
from aiogram import Bot, F, Router
from aiogram.enums import ContentType
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, BotCommand, ReplyKeyboardRemove
from aiogram.utils.formatting import Text, Code, Bold

import Config
from Config import ADMIN, TOKEN, CARD_NUMBER, FAST_DELIVERY, SLOW_DELIVERY
from database import Users, UserType, Orders
from database.Categories import CategoriesService
from database.OrderPhotos import OrderPhotosService
from handlers import AdminRouters
from handlers.States import OrderState, OrderPhotos, CancelOrder
from handlers.Translation import _
from handlers.keyboard import order_accept, instagram_button, language_markup, all_categories, delivery_type
from middleware.LoggingMiddleware import LoggingMiddleware
from middleware.Middleware import Middleware


bot = Bot(token=TOKEN)
bot_commands = [
    BotCommand(command="/start", description="Botni boshlash"),
    BotCommand(command="/lang", description="Tilni o'zgartirish")]


router = Router()
router.message.middleware.register(Middleware())
router.callback_query.middleware.register(Middleware())
router.sub_routers.append(AdminRouters.route)
router.message.middleware.register(LoggingMiddleware())
router.callback_query.middleware.register(LoggingMiddleware())

users_service = Users.UsersService()
user_type_service = UserType.UserTypeService()
orders_service = Orders.OrdersService()
order_photos_service = OrderPhotosService()
category_service = CategoriesService()


@router.message(Command('lang'))
async def change_language(message: Message) -> None:
    await select_language(message)


async def welcome_customer(user_id: int, message: Message, lang: str):
    content = Text(
        Text(_("Уважаемый пользователь, вы зарегистрировались в боте Ismo Group.\n", lang)),
        Text(
            _("\nС помощью этого бота вы можете искать и скачивать фотографии со своей свадьбы, дня рождения или мероприятия.", lang)
        )
    )
    await message.answer(**content.as_kwargs())
    await message.answer(
        Bold(_("Чтобы начать заказ, вы можете начать с выбора категории ниже.", lang)).as_markdown(),
        reply_markup=all_categories("order_"),
        parse_mode='MarkdownV2'
    )


@router.message(Command("admin"))
async def command_admin_handler(message: Message, state: FSMContext, lang: str) -> None:
    await bot.send_message(
        chat_id=message.from_user.id, text=_("Если у вас возникнут какие-либо проблемы с ботом, пожалуйста, свяжитесь с @lazizkhan1 !", lang))


@router.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext, lang: str, user: dict | None = None) -> None:

    await state.clear()

    await bot.set_my_commands(bot_commands)

    if user is None:
        user_type = user_type_service.getAdminType() if message.from_user.id == ADMIN else user_type_service.getCustomerType()
        users_service.create(
            message.from_user.id,
            message.from_user.username or "",
            message.from_user.language_code or Config.DEFAULT_LANGUAGE,
            user_type
        )
        await select_language(message)
        return

    if user['user_type'] == user_type_service.getCustomerType():
        await welcome_customer(message.from_user.id, message, lang)
    else:
        await AdminRouters.command_start_handler(message, lang)


async def select_language(message: Message):
    await bot.send_message(
        chat_id=message.from_user.id,
        text="🇺🇿 Iltimos tilni tanlang! \n🇷🇺 Пожалуйста, выберите язык!",
        reply_markup=language_markup()
    )


@router.callback_query(F.data.startswith('lang_'))
async def choose_language(query: CallbackQuery) -> None:
    lang = query.data.split('_')[-1]
    users_service.setLanguage(query.from_user.id, lang)
    await query.message.delete()
    user = users_service.getById(query.from_user.id)
    await query.answer(_("Язык успешно изменен!✅", lang))
    if user and user['user_type'] == user_type_service.getCustomerType():
        await welcome_customer(query.from_user.id, query.message, lang)
    else:
        await AdminRouters.command_start_handler(query.message, lang)


# ORDER

@router.callback_query(F.data.startswith('order_category:'))
async def order_category_select(query: CallbackQuery, state: FSMContext, lang: str) -> None:
    category_id = int(query.data.split(':')[-1])
    await state.update_data(category_id=category_id)

    await state.set_state(OrderState.ceremony_date)
    await query.message.edit_text(_("Введите дату церемонии! \nНапример: (24.10.2024)", lang))
    await query.answer(_("Категория выбрана!", lang))

    


@router.message(OrderState.ceremony_date)
async def order_ceremony_date(message: Message, state: FSMContext, lang: str) -> None:
    date_str = message.text.strip().split('.')
    if len(date_str) != 3:
        await message.answer(_("Неверный формат даты!", lang) + "\n" + _("Введите дату церемонии! \nНапример: (24.10.2024)", lang))
        return
    try:
        date = datetime.date(int(date_str[2]), int(date_str[1]), int(date_str[0]))
        await state.update_data(ceremony_date=date.strftime('%Y-%m-%d'))
        await state.set_state(OrderState.video_note_id)
        await message.answer(_("Пожалуйста, отправьте видеокружок (круглое видео) с вашим лицом не менее 3 секунд! \nНам нужно это видео, чтобы мы могли узнать вас по фотографии!", lang))
    except Exception:
        await message.answer(_("Неверный формат даты!", lang) + "\n" + _("Введите дату церемонии! \nНапример: (24.10.2024)", lang))


@router.message(OrderState.video_note_id)
async def order_video_note(message: Message, state: FSMContext, lang: str) -> None:
    if message.content_type != ContentType.VIDEO_NOTE or message.video_note.duration < 3:
        await message.answer(_("Пожалуйста, отправьте видеокружок (круглое видео) с вашим лицом не менее 3 секунд! \nНам нужно это видео, чтобы мы могли узнать вас по фотографии!", lang))
        return
    video_note_id = message.video_note.file_id
    await state.update_data(video_note_id=video_note_id)

    await state.set_state(OrderState.delivery_type)
    await bot.send_message(
        chat_id=message.from_user.id,
        text=_("Выберите скорость доставки заказа:", lang),
        reply_markup=delivery_type(lang)
    )


@router.callback_query(F.data.startswith('delivery_'))
async def order_delivery_type_select(query: CallbackQuery, state: FSMContext, lang: str) -> None:
    del_type = query.data.split('_')[-1]
    price = FAST_DELIVERY if del_type == 'fast' else SLOW_DELIVERY
    await state.update_data(delivery_type=del_type, price=price)

    await state.set_state(OrderState.cheque_id)

    data = await state.get_data()

    content = Text(
        _("Стоимость заказа: ", lang), Bold(f"{price:,}".replace(",", " ")), Text(_(" сум\n", lang)),
        _("Оплатите на карту: ", lang), Code(CARD_NUMBER), Text("\n"),
        Bold(_("Отправьте чек оплаты!", lang))
    )
    await query.message.edit_text(**content.as_kwargs())
    await query.answer(_("Доставка выбрана!", lang))



@router.message(OrderState.cheque_id)
async def order_cheque_id(message: Message, state: FSMContext, lang: str) -> None:
    if message.content_type != ContentType.PHOTO:
        await message.answer(_("Отправьте фото!", lang))
        return

    cheque_id = message.photo[-1].file_id
    data = await state.get_data()

    order = orders_service.create(
        message.from_user.id,
        data['category_id'],
        data['ceremony_date'],
        data['video_note_id'],
        cheque_id
    )

    category = category_service.getById(data['category_id'])
    cat_name = category['name'] if category else str(data['category_id'])
    del_speed = _("Быстрая (2 часа)", lang) if data.get('delivery_type') == 'fast' else _("Обычная (24 часа)", lang)

    # Notify admins
    admins = users_service.getAllByUserType(user_type_service.getAdminType())
    admin_ids = {ADMIN}
    for a in admins:
        admin_ids.add(a['id'])

    for admin_id in admin_ids:
        try:
            await bot.send_video_note(chat_id=admin_id, video_note=data['video_note_id'])
            await bot.send_photo(
                chat_id=admin_id,
                photo=cheque_id,
                caption=f"{_('Новый заказ!\nID: ', lang)}{message.from_user.id}\n"
                        f"Order ID: {order['id']}\n"
                        f"{_('Категория: ', lang)}{cat_name}\n"
                        f"{_('Дата: ', lang)}{data['ceremony_date']}\n"
                        f"{_('Доставка: ', lang)}{del_speed}",
                reply_markup=order_accept(order['id'], lang)
            )
        except Exception as e:
            print(f"Error notifying admin {admin_id}: {e}")

    await state.clear()
    await message.answer(
        _("Заказ успешно оформлен! Наши администраторы отправят вам ваши фотографии как можно скорее.", lang)
    )


@router.callback_query(F.data.startswith('accept_order:'))
async def accept_order(query: CallbackQuery, state: FSMContext, lang: str) -> None:
    order_id = int(query.data.split(':')[-1])
    order = orders_service.getById(order_id)
    if not order or order['status'] != Orders.OrderStatus.PENDING:
        await query.answer(_("Заказ уже принят или отменен!", lang))
        return

    orders_service.acceptOrder(order_id)
    await state.update_data(order_id=order_id)
    await state.set_state(OrderPhotos.photos)
    await query.message.answer(_("Пожалуйста, отправьте фотографии пользователя!", lang))
    await query.answer(_("Заказ принят!", lang))
    await bot.set_my_commands([
        BotCommand(command="/done", description="Rasmlarni yuborishni yakunlash")
    ])

@router.message(OrderPhotos.photos)
async def order_photos_upload(message: Message, state: FSMContext, lang: str) -> None:
    data = await state.get_data()
    order_id = data.get('order_id')

    if message.content_type in (ContentType.DOCUMENT, ContentType.PHOTO):
        file_id = message.photo[-1].file_id if message.content_type == ContentType.PHOTO else message.document.file_id
        order_photos_service.add_order_photo(order_id, file_id)
        await message.answer(_("Фото добавлено!", lang))
        return

    if message.text == "/done":
        order = orders_service.completeOrder(order_id)
        photos = order_photos_service.get_order_photos(order_id)
        await bot.set_my_commands(bot_commands)
        for item in photos:
            try:
                await bot.send_photo(chat_id=order['user_id'], photo=item['photo_id'])
            except Exception:
                await bot.send_document(chat_id=order['user_id'], document=item['photo_id'])

        await state.clear()
        await bot.send_message(
            chat_id=order['user_id'],
            text=_("Если хотите, можете подписаться на нашу страницу в Инстаграм!", lang),
            reply_markup=instagram_button(lang)
        )
        await message.answer(_("Заказ успешно завершен и фотографии отправлены!", lang))


@router.callback_query(F.data.startswith('cancel_order_admin:'))
async def cancel_order_admin(query: CallbackQuery, state: FSMContext, lang: str) -> None:
    order_id = int(query.data.split(':')[-1])
    await state.set_state(CancelOrder.reason)
    await state.update_data(order_id=order_id)
    await query.message.answer(_("Введите причину отмены заказа:", lang))


@router.message(CancelOrder.reason)
async def cancel_order_reason(message: Message, state: FSMContext, lang: str) -> None:
    data = await state.get_data()
    await state.clear()
    order = orders_service.getById(data['order_id'])
    if order:
        orders_service.cancelOrder(order['id'], message.text)
        await message.answer(_("Заказ был отменен!", lang))
        try:
            await bot.send_message(
                chat_id=order['user_id'],
                text=_("Ваш заказ был отменен по причине: ", lang) + message.text
            )
        except Exception:
            pass


