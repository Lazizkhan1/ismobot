from aiohttp import ClientTimeout
from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession

from Config import TOKEN


if not TOKEN:
    raise ValueError("TOKEN environment variable is required")

session = AiohttpSession(timeout=ClientTimeout(total=60, connect=15, sock_read=15))
bot = Bot(token=TOKEN, session=session)
