import logging
from logging.handlers import TimedRotatingFileHandler
from logging.handlers import TimedRotatingFileHandler
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery


class LoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Extract user info if available
        user = data.get("event_from_user")
        user_id = user.id if user else "Unknown"
        username = user.username if user else "Unknown"
        user_full_name = f"{user.first_name} {user.last_name}" if user else "Unknown"


        # Identify interaction type
        logger.debug(event.model_dump_json(indent=4))
        if isinstance(event, Message):
            logger.warning(f"Message from @{username} | {user_full_name} ({user_id}): {event.text}")
        elif isinstance(event, CallbackQuery):
            logger.warning(f"Callback from @{username} | {user_full_name} ({user_id}): {event.data}")
        else:
            logger.warning(f"Interaction from @{username} | {user_full_name} ({user_id}): {type(event).__name__}")
            
        # Continue execution to the actual handler
        return await handler(event, data)
