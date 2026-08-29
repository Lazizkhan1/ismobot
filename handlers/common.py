import logging

from aiogram.utils.keyboard import KeyboardBuilder

import Config
from aiogram import F, Router
from aiogram.enums import ParseMode, ChatType
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, KeyboardButton
from aiogram.utils.deep_linking import decode_payload
from aiogram.utils.formatting import Bold, Text

from bot_instance import bot
from Config import ADMIN
from database import Users, UserType
from database.models import User
from database.Referrals import ReferralsService
from handlers import admin_menu
from handlers.Translation import _
from handlers.constants import bot_commands
from handlers.keyboard import language_markup, main_menu_keyboard

router = Router()

users_service = Users.UsersService()
user_type_service = UserType.UserTypeService()
referrals_service = ReferralsService()


@router.message(Command("lang"))
async def change_language(message: Message) -> None:
    await select_language(message)


async def welcome_customer(message: Message, lang: str):
    await message.answer(
        _("👋 Привет! Что хотите сделать?", lang),
        reply_markup=main_menu_keyboard(lang),
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
        command: CommandObject,
        state: FSMContext,
        lang: str,
        user: User,
) -> None:
    await state.clear()

    if message.chat.type == ChatType.PRIVATE and message.from_user:
        # Handle referral deep link
        if command.args:
            try:
                payload = decode_payload(command.args)
                referrer_id = int(payload)
                if referrer_id != user.id and not user.referrer_id:
                    if not await referrals_service.exists(user.id):
                        await Users.set_referrer(user.id, referrer_id)
                        await referrals_service.create(referrer_id, user.id)
                        user.referrer_id = referrer_id
                        logging.info("User %s referred by %s", user.id, referrer_id)
            except Exception as e:
                logging.warning("Error processing referral deep link: %s", e)

        if message.from_user.id == ADMIN:
            await bot.set_my_commands(bot_commands)
            await admin_menu.command_start_handler(message, lang)
        else:
            if user.lang == "en":
                await select_language(message)
            else:

                await welcome_customer(message, lang)


async def select_language(message: Message):
    await bot.send_message(
        chat_id=message.from_user.id,
        text="🇺🇿 Iltimos tilni tanlang! \n🇷🇺 Пожалуйста, выберите язык!",
        reply_markup=language_markup(),
    )


@router.callback_query(F.data.startswith("lang_"))
async def choose_language(query: CallbackQuery) -> None:
    lang = query.data.split("_")[-1]
    await query.message.delete()
    user = await Users.getById(query.from_user.id)
    if user:
        user.lang = lang
        user = await Users.update_user(user)
    await query.answer(_("Язык успешно изменен!✅", lang))
    if user and user.user_type == UserType.UserTypeEnum.CUSTOMER:
        await welcome_customer(query.message, lang)
    else:
        await admin_menu.command_start_handler(query.message, lang)
