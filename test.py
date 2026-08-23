import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ChatType
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message, ReplyParameters

from Config import CHANNEL_ID, GROUP_ID, TOKEN, ADMIN
from database import Users
from database.UserType import UserTypeEnum

TOKEN = TOKEN
router = Router()
bot = Bot(token=TOKEN)


@router.message(CommandStart(), F.chat.type == ChatType.PRIVATE)
async def cmd_start(message: Message):
    user_photo = await bot.get_user_profile_photos(user_id=message.from_user.id, limit=1)
    photo_id = None if user_photo.total_count == 0 else user_photo.photos[0][-1].file_id

    text = (
        f"#new_user | {message.from_user.id} |"
        f"\nYangi foydalanuvchi: {message.from_user.full_name}"
        f"\nFoydalanuvchi ID: {message.from_user.id}"
        f"\nFoydalanuvchi username: @{message.from_user.username}"
        f"\nSana: {message.date.strftime('%Y-%m-%d %H:%M:%S')}"
    )
    new_message = None
    if photo_id:
        new_message = await bot.send_photo(CHANNEL_ID, photo=photo_id, caption=text)
    else:
        new_message = await bot.send_message(CHANNEL_ID, text=text)

    await Users.UsersService().create_user(
        Users.User(
            id=message.from_user.id,
            username=message.from_user.username,
            full_name=message.from_user.full_name,
            channel_message_id=new_message.message_id,
            lang="en",
            user_type=UserTypeEnum.ADMIN if message.from_user.id == ADMIN else UserTypeEnum.CUSTOMER
        )
    )

    await message.answer("Hello! Press the button below:")


@router.message(F.chat.id == GROUP_ID and F.text.startswith("#new_user") and F.forward_from_chat.id == CHANNEL_ID)
async def group_handler(message: Message):
    user_id = int(message.text.split("|")[1].strip())
    user = await Users.getById(user_id)
    if not user:
        print(f"User with ID {user_id} not found in the database.")
    elif isinstance(user, Users.User):
        original_user: Users.User = user

        original_user.group_message_id = message.message_id
        await Users.update_user(original_user)


@router.message(F.chat.type == "private")
async def private_handler(message: Message):
    user = await Users.getById(message.from_user.id)
    if not user or not isinstance(user, Users.User):
        return

    await bot.send_message(chat_id=GROUP_ID, reply_to_message_id=user.group_message_id, reply_parameters=ReplyParameters(message_id=message.message_id), text="")
    await message.answer("Message sent to the group chat.")


@router.message(F.chat.type == ChatType.PRIVATE)
async def echo(message: Message):
    await bot.send_message(chat_id=GROUP_ID, text="", reply_parameters=ReplyParameters(message_id=message.message_id, chat_id=GROUP_ID))
    await message.answer("Message sent to the group chat.")



async def main():
    # await bot.delete_webhook()
    dp = Dispatcher()
    dp.include_router(router)

    await dp.start_polling(bot, drop_pending_updates=True)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
