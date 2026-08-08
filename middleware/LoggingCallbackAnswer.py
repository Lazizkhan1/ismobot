import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

logger = logging.getLogger(__name__)
from aiogram.utils.callback_answer import CallbackAnswerMiddleware


class LoggingCallbackAnswer(CallbackAnswerMiddleware):
    async def __call__(self,
            handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: dict[str, Any]) -> Any:
        # Log the callback answer details
        logger.info(f"Callback Answer: {self}")
        return await super().__call__(handler, event, data)