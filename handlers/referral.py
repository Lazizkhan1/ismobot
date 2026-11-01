from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.types import Message, InlineKeyboardButton, SwitchInlineQueryChosenChat, InlineKeyboardMarkup

from handlers.Translation import _

_bot_username: str | None = None


async def get_referral_link(bot: Bot, user_id: int) -> str:
    global _bot_username
    if not _bot_username:
        bot_user = await bot.get_me()
        _bot_username = bot_user.username
    return f"https://t.me/{_bot_username}?start={user_id}"


async def send_referral_message(bot: Bot, chat_id: int, user_id: int, lang: str) -> Message:
    link = await get_referral_link(bot, user_id)
    template = _(
        "🌟 <b>Пригласите друзей в Ismo Group!</b>\n\n"
        "Отправьте эту ссылку друзьям и знакомым, чтобы они тоже могли легко найти и скачать свои фотографии с мероприятий:\n"
        "👉 {referral_link}",
        lang,
    )
    text = template.format(referral_link=link)
    return await bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode=ParseMode.HTML,
    )
