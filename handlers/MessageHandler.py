import datetime

import aiogram.types
from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ContentType
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InputMediaPhoto, BotCommand
from aiogram.utils.formatting import Text, Code, Bold
from aiogram.utils.media_group import MediaGroupBuilder
from aiohttp import web

import Config
from Config import ADMIN, TOKEN, CARD_NUMBER, GROUP_PHOTO, SINGLE_PHOTO
from database import Users, UserType, Orders
from database.Categories import CategoriesService
from database.CategoryType import CategoryTypeService
from database.Database import Database
from database.OrderPhotos import OrderPhotosService
from handlers import AdminRouters, ModeratorRouters
from handlers.States import OrderState, OrderPhotos, CancelOrder
from handlers.Translation import _
from handlers.keyboard import all_category_types, person_count, order_accept, instagram_button, \
    language_markup
from middleware.Middleware import Middleware, ModeratorMiddleware

app = web.Application()
bot = Bot(token=TOKEN)
dp = Dispatcher()
db = Database()

mod_route = Router()
mod_route.message.middleware.register(ModeratorMiddleware())
dp.sub_routers.append(mod_route)
dp.sub_routers.append(AdminRouters.route)
dp.update.middleware.register(Middleware())
dp.sub_routers.append(ModeratorRouters.router)
users_service = Users.UsersService()
user_type_service = UserType.UserTypeService()
orders_service = Orders.OrdersService()
order_photos_service = OrderPhotosService()
category_service = CategoriesService()
category_type_service = CategoryTypeService()

WEB_SERVER_HOST = Config.WEB_SERVER_HOST
# Port for incoming request from reverse proxy. Should be any available port
WEB_SERVER_PORT = Config.WEB_SERVER_PORT

# Path to webhook route, on which Telegram will send requests
WEBHOOK_PATH = Config.WEBHOOK_PATH
# Secret key to validate requests from Telegram (optional)
WEBHOOK_SECRET = Config.WEBHOOK_SECRET
# Base URL for webhook will be used to generate webhook URL for Telegram,
# in this example it is used public DNS with HTTPS support
BASE_WEBHOOK_URL = Config.BASE_WEBHOOK_URL


# TODO: User language instead of message.from_user.language_code
# TODO: Category type lang
# TODO: Add seperate price for many or single person
# TODO: 

@dp.message(
    Command('lang')
)
async def change_language(message: aiogram.types.Message) -> None:
    await select_language(message)


async def welcome_customer(user_id, message, lang):
    content = Text(
        Text(_("Уважаемый пользователь, вы зарегистрировались в боте Ismo Group.\n", lang)),
        Bold(_("Ваш идентификационный номер: ", lang)),
        Code(user_id),
        Text(
            _("\nС помощью этого бота вы можете искать и скачивать фотографии со своей свадьбы, дня рождения или мероприятия.",
              lang))
    )
    await message.answer(**content.as_kwargs())
    await message.answer(
        Bold(_("Чтобы начать заказ, вы можете начать с выбора типа здания ниже. ", lang)).as_markdown(),
        reply_markup=all_category_types(lang, "order_"), parse_mode='MarkdownV2')


@dp.message(
    CommandStart()
)
async def command_start_handler(message: aiogram.types.Message, state: FSMContext, lang: str) -> None:
    user: dict = users_service.getById(message.from_user.id)
    if user is None:
        user_type = user_type_service.getAdminType() if message.from_user.id == ADMIN else user_type_service.getCustomerType()
        users_service.create(message.from_user.id, message.from_user.username,
                             message.from_user.language_code, user_type)
        await select_language(message)
        return

    user_type = user['user_type']
    if user_type == user_type_service.getCustomerType():
        await welcome_customer(message.from_user.id, message, lang)
        await state.set_state(OrderState.category_type)
    else:
        await AdminRouters.command_start_handler(message, lang)


async def select_language(message: aiogram.types.Message):
    await bot.send_message(chat_id=message.from_user.id,
                           text="🇺🇿 Iltimos tilni tanlang! \n🇷🇺 Пожалуйста, выберите язык! \n🇺🇸 Please select a language!",
                           reply_markup=language_markup())


@dp.callback_query(
    F.data.startswith('lang')
)
async def choose_language(query: aiogram.types.CallbackQuery) -> None:
    lang = query.data.split('_')[-1]
    users_service.setLanguage(query.from_user.id, lang)
    await query.message.delete()
    await welcome_customer(query.from_user.id, query.message, lang)


@dp.callback_query(
    F.data.startswith('order_category_type')
)
async def order_category_type(query: aiogram.types.CallbackQuery, state: FSMContext, lang: str) -> None:
    category_type_id = int(query.data.split(':')[-1])
    await state.update_data(category_type_id=category_type_id)
    await state.set_state(OrderState.message_ids)
    message_ids = []
    for category in category_service.getByType(category_type_id):
        message_ids.append(
            (await bot.send_photo(chat_id=query.from_user.id, photo=category['photo_id'],
                                  reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                      [aiogram.types.InlineKeyboardButton(
                                          text=f"{category['name']}",
                                          callback_data=f"order_category:{category['id']}")]
                                  ]
                                  )
                                  )
             ).message_id
        )
    await state.update_data(message_ids=message_ids)
    await state.set_state(OrderState.category)


@dp.callback_query(
    F.data.startswith('order_category')
)
async def order_category(query: aiogram.types.CallbackQuery, state: FSMContext, lang: str) -> None:
    category_id = int(query.data.split(':')[-1])
    await state.update_data(category_id=category_id)
    for message_id in (await state.get_data())['message_ids']:
        if message_id != query.message.message_id:
            await bot.delete_message(chat_id=query.from_user.id, message_id=message_id)
    await state.set_state(OrderState.ceremony_date)
    await query.message.answer(_("Введите дату церемонии!\nНапример: (24.10.2024)", lang))


@dp.message(
    OrderState.ceremony_date
)
async def order_ceremony_date(message: aiogram.types.Message, state: FSMContext, lang: str) -> None:
    date_str = message.text.split('.')
    if len(date_str) != 3:
        await message.answer(_("Неверный формат даты!", lang))
        return
    try:
        date = datetime.datetime(int(date_str[2]), int(date_str[1]), int(date_str[0]))
        await state.update_data(ceremony_date=date)
        await state.set_state(OrderState.single_person)
        media_group = [
            InputMediaPhoto(media=GROUP_PHOTO),
            InputMediaPhoto(media=SINGLE_PHOTO)
        ]
        await bot.send_media_group(chat_id=message.from_user.id, media=media_group)
        await message.answer(**Bold(
            _("На одного человека в едином тарифе Вам будет представлена только 1 сделанная Вами фотография. И большинство тарифов содержат фотографии людей, которых вы отметили, как показано на отправленном вами изображении, или всех людей на изображении, если вы не отметили людей на изображении!",
              lang)).as_kwargs(),
                             reply_markup=person_count(lang))
    except:
        await message.answer(_("Неверный формат даты!", lang))


@dp.callback_query(
    F.data.endswith('_person')
)
async def order_person_count(query: aiogram.types.CallbackQuery, state: FSMContext, lang: str) -> None:
    single = str(query.data.split('_')[0]) == "single"
    await state.update_data(single_person=single)
    await state.set_state(OrderState.photo_id)
    if not single:
        await query.message.answer(_("Отправьте свою фотографию, как многие!", lang))
    else:
        await query.message.answer(_("Отправьте свою фотографию, на которой должно быть видно ваше лицо.", lang))


@dp.message(
    OrderState.photo_id
)
async def order_photo_id(message: aiogram.types.Message, state: FSMContext, lang: str) -> None:
    if message.content_type is not ContentType.PHOTO:
        single = (await state.get_data())['single_person']
        if not single:
            await message.answer(_("Отправьте свою фотографию, как многие!", lang))
        else:
            await message.answer(_("Отправьте свою фотографию, на которой должно быть видно ваше лицо.", lang))
        return
    photo_id = message.photo[-1].file_id
    await state.update_data(photo_id=photo_id)
    await state.set_state(OrderState.cheque_id)
    data = await state.get_data()
    category = category_service.getById(data['category_id'])
    category_type = category_type_service.getById(category['category_type'])
    price = category_type['group_price'] if not data['single_person'] else category_type['single_price']
    content = Text(_("Стоимость заказа: ", lang), Bold(price), Text(_(" сум\n", lang)),
                   Text(_("Оплатите на карту: ", lang)), Code(CARD_NUMBER), Text(_("\n", lang)),
                   Bold(_("Отправьте чек оплаты!", lang)))
    await message.answer(**content.as_kwargs())


@dp.message(
    OrderState.cheque_id
)
async def order_cheque_id(message: aiogram.types.Message, state: FSMContext, lang: str) -> None:
    if message.content_type is not ContentType.PHOTO:
        await message.answer(_("Отправьте фото!", lang))
        return
    cheque_id = message.photo[-1].file_id
    await state.update_data(cheque_id=cheque_id)
    data = await state.get_data()
    order = orders_service.create(message.from_user.id, data['category_id'], data['ceremony_date'],
                                  data['single_person'],
                                  data['photo_id'], data['cheque_id'])
    moderators = users_service.getAllByUserType(user_type_service.getModeratorType())
    for moderator in moderators:
        await bot.send_message(chat_id=moderator['id'],
                               text=_("Новый заказ!\nID: ", lang) + f"{message.from_user.id}\n" + _("Категория: ",
                                                                                                    lang) + f"{data['category_id']}\n" + _(
                                   "Дата: ", lang) + f"{data['ceremony_date']}\n" + _("Один человек: ",
                                                                                      lang) + f"{data['single_person']}",
                               reply_markup=order_accept(order['id'], lang))
    await state.clear()
    await state.set_state(OrderPhotos.order_id)
    await message.answer(
        _("Заказ успешно оформлен! Наши администраторы отправят вам ваши фотографии как можно скорее.", lang))


@dp.callback_query(
    F.data.startswith('accept_order:')
)
async def accept_order(query: aiogram.types.CallbackQuery, state: FSMContext, lang: str) -> None:
    order_id = query.data.split(':')[-1]
    if orders_service.getById(order_id)['moderator_id'] is not None:
        await query.message.delete()
        return
    order_id = query.data.split(':')[-1]
    order = orders_service.setModeratorId(order_id, query.from_user.id)
    media = MediaGroupBuilder()
    media.add_photo(order['photo_id'])
    media.add_photo(order['cheque_id'])

    # please send the photos to the user
    await query.message.answer(_("Пожалуйста, отправьте фотографии пользователя!", lang))
    await state.update_data(order_id=order_id)
    await state.set_state(OrderPhotos.photos)
    await query.message.delete()
    await bot.send_media_group(chat_id=query.from_user.id, media=media.build())


@dp.message(
    OrderPhotos.photos
)
async def order_photos(message: aiogram.types.Message, state: FSMContext, lang: str) -> None:
    data = await state.get_data()
    if message.content_type is ContentType.DOCUMENT or message.content_type is ContentType.PHOTO:
        file_id = message.photo[-1].file_id if message.content_type is ContentType.PHOTO else message.document.file_id
        await state.set_state(OrderPhotos.photos)
        order_photos_service.add_order_photo(data['order_id'], file_id, message.content_type)
        return
    elif message.text == "/cancel":
        user = users_service.getById(message.from_user.id)
        if user['user_type'] != user_type_service.getModeratorType():
            return
        data = await state.get_data()
        if data is None:
            print("data none")
            return
        if data['order_id'] is not None:
            await state.clear()
            await state.set_state(CancelOrder.order_id)
            await state.update_data(order_id=data['order_id'])
            await state.set_state(CancelOrder.reason)
            await message.answer(_("Введите причину отмены заказа:", lang))
        return

    order = orders_service.completeOrder(data['order_id'])

    for msg in order_photos_service.get_order_photos(order['id']):
        if msg['type'] == ContentType.PHOTO:
            await bot.send_photo(chat_id=order['user_id'], photo=msg['photo_id'])
        else:
            await bot.send_document(chat_id=order['user_id'], document=msg['photo_id'])
    await state.clear()

    await bot.send_message(chat_id=order['user_id'],
                           text=_("Если хотите, можете подписаться на нашу страницу в Инстаграм!", lang),
                           reply_markup=instagram_button(lang))
    await message.answer(_("Фото добавлено!", lang))


async def send_error_message(message: aiogram.types.Message, error: Exception, lang: str) -> None:
    await message.answer(_(f"Произошла ошибка: {error}", lang))


@dp.message(
    CancelOrder.reason
)
async def cancel_order_reason(message: aiogram.types.Message, state: FSMContext, lang: str) -> None:
    data = await state.get_data()
    await state.clear()
    order = orders_service.getById(data['order_id'])
    await orders_service.cancelOrder(order['id'], message.text)
    await message.answer(_("Заказ был отменен!", lang))
    await bot.send_message(chat_id=order['user_id'], text=_("Ваш заказ был отменен по причине: ", lang) + message.text)


@mod_route.message(
    Command('orders')
)
async def orders(message: aiogram.types.Message, lang: str) -> None:
    orders = orders_service.getByStatus(Orders.OrderStatus.PENDING)
    if len(orders) == 0:
        await message.answer(_("Нет заказов!", lang))
        return
    for order in orders:
        category = category_service.getById(order['category_id'])
        category_type = category_type_service.getById(category['category_type'])
        price = category_type['group_price'] if not order['single_person'] else category_type['single_price']
        await message.answer(text=_("ID: ", lang) + f"{order['id']}\n" + _("Категория: ", lang) + f"{category['name']}\n" + _("Дата: ", lang) + f"{order['ceremony_date']}\n" + _("Один человек: ", lang) + f"{order['single_person']}\n" + _("Price: ", lang) + f"{price}\n",
            reply_markup=order_accept(order['id'], lang))


async def start_bot(bot: Bot):
    # await bot.set_webhook(f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}", secret_token=WEBHOOK_SECRET)
    await bot.delete_webhook()
    await bot.set_my_commands([BotCommand(command="/start", description="Botni boshlash"), BotCommand(command="/lang", description="Tilni o'zgartirish"), BotCommand(command="/help", description="Yordam olish")], language_code='uz')
    await bot.send_message(ADMIN, text=_("Бот запущен успешно!", 'ru'))


async def stop_bot(bot: bot):
    await bot.send_message(ADMIN, text=_("Бот остановил свою работу!", 'ru'))


async def main() -> None:

    dp.startup.register(start_bot)
    dp.shutdown.register(stop_bot)
    await dp.start_polling(bot)


