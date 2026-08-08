import logging
import os
import sys
from sys import stdout
from logging import DEBUG, WARNING, basicConfig, INFO

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from Config import ADMIN, TOKEN, WEBHOOK_SECRET, WEBHOOK_PATH, WEB_SERVER_HOST, WEB_SERVER_PORT, BASE_WEBHOOK_URL

from handlers.MessageHandler import router
from handlers.Translation import _
from aiohttp import web
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey

from middleware.LoggingMiddleware import LoggingMiddleware

dp = Dispatcher()


def _resolve_base_webhook_url() -> str:
    if len(sys.argv) > 1 and sys.argv[1]:
        return sys.argv[1].rstrip("/")
    if os.getenv("BASE_WEBHOOK_URL"):
        return os.getenv("BASE_WEBHOOK_URL").rstrip("/")
    return BASE_WEBHOOK_URL.rstrip("/")


def run_webhook():
    from handlers.MessageHandler import bot as bot_inst
    webhook_path = WEBHOOK_PATH if WEBHOOK_PATH.startswith("/") else f"/{WEBHOOK_PATH}"
    base_webhook_url = _resolve_base_webhook_url()
    if not base_webhook_url:
        raise ValueError("BASE_WEBHOOK_URL environment variable is required for webhook mode")
    webhook_url = f"{base_webhook_url}{webhook_path}"

    app = web.Application()
    dp.callback_query.middleware.register(LoggingMiddleware())
    dp.startup.register(start_bot)
    dp.shutdown.register(stop_bot)
    dp.include_router(router)
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot_inst,
        secret_token=WEBHOOK_SECRET,
    )
    webhook_requests_handler.register(app, path=webhook_path)
    setup_application(app, dp, bot=bot_inst)

    async def on_startup(_: web.Application):
        await bot_inst.set_webhook(url=webhook_url, secret_token=WEBHOOK_SECRET)

    async def on_shutdown(_: web.Application):
        await bot_inst.delete_webhook(drop_pending_updates=True)

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)



async def start_bot():
    from handlers.MessageHandler import bot as bot_inst
    await bot_inst.set_my_commands([
        BotCommand(command="/start", description="Botni boshlash"),
        BotCommand(command="/lang", description="Tilni o'zgartirish"),
        BotCommand(command="/admin", description="Admin bilan bog'lanish")
        
    ], language_code='uz')
    try:
        await bot_inst.send_message(ADMIN, text=_("Бот запущен успешно!", 'ru'))
    except Exception:
        pass


async def stop_bot():
    from handlers.MessageHandler import bot as bot_inst
    try:
        #await dp.storage.close()
        await bot_inst.send_message(ADMIN, text=_("Бот остановил свою работу!", 'ru'))
    except Exception:
        pass

if __name__ == '__main__':
    logging.basicConfig(
    filename='app.log', 
    encoding='utf-8', 
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode='a'  # 'a' to append logs, 'w' to overwrite the file on every run
)

    if len(sys.argv) > 1 and sys.argv[1]:
        os.environ['BASE_WEBHOOK_URL'] = sys.argv[1].rstrip('/')

    run_webhook()

