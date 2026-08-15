import Config
from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.formatting import Bold, Text

from bot_instance import bot
from Config import ADMIN
from database import Users, UserType
from handlers import admin_menu
from handlers.Translation import _
from handlers.constants import bot_commands
from handlers.keyboard import all_categories, language_markup

router = Router()

users_service = Users.UsersService()
user_type_service = UserType.UserTypeService()


@router.message(Command("lang"))
async def change_language(message: Message) -> None:
    await select_language(message)


async def welcome_customer(user_id: int, message: Message, lang: str):
    content = Text(
        Text(_("Уважаемый пользователь, вы зарегистрировались в боте Ismo Group.\n", lang)),
        Text(
            _(
                "\nС помощью этого бота вы можете искать и скачивать фотографии со своей свадьбы, дня рождения или мероприятия.",
                lang,
            )
        ),
    )
    await message.answer(**content.as_kwargs())
    await message.answer(
        Bold(_("Чтобы начать заказ, вы можете начать с выбора категории ниже.", lang)).as_html(),
        reply_markup=await all_categories("order_"),
        parse_mode=ParseMode.HTML,
    )


@router.message(Command("admin"))
async def command_admin_handler(message: Message, state: FSMContext, lang: str) -> None:
    await bot.send_message(
        chat_id=message.from_user.id,
        text=_(
            "Если у вас возникнут какие-либо проблемы с ботом, пожалуйста, свяжитесь с @ismo_group_admin !",
            lang,
        ),
    )


@router.message(CommandStart())
async def command_start_handler(
    message: Message,
    state: FSMContext,
    lang: str,
    user: dict | None = None,
) -> None:
    await state.clear()
    await bot.set_my_commands(bot_commands)

    if user is None:
        user_type = (
            user_type_service.getAdminType()
            if message.from_user.id == ADMIN
            else user_type_service.getCustomerType()
        )
        await users_service.create(
            message.from_user.id,
            message.from_user.username or "",
            message.from_user.language_code or Config.DEFAULT_LANGUAGE,
            user_type,
        )
        await select_language(message)
        return

    if user["user_type"] == user_type_service.getCustomerType():
        await welcome_customer(message.from_user.id, message, lang)
    else:
        await admin_menu.command_start_handler(message, lang)


async def select_language(message: Message):
    await bot.send_message(
        chat_id=message.from_user.id,
        text="🇺🇿 Iltimos tilni tanlang! \n🇷🇺 Пожалуйста, выберите язык!",
        reply_markup=language_markup(),
    )


@router.callback_query(F.data.startswith("lang_"))
async def choose_language(query: CallbackQuery) -> None:
    lang = query.data.split("_")[-1]
    await users_service.setLanguage(query.from_user.id, lang)
    await query.message.delete()
    user = await users_service.getById(query.from_user.id)
    await query.answer(_("Язык успешно изменен!✅", lang))
    if user and user["user_type"] == user_type_service.getCustomerType():
        await welcome_customer(query.from_user.id, query.message, lang)
    else:
        await admin_menu.command_start_handler(query.message, lang)
