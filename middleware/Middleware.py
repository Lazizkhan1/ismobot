from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from Config import ADMIN, DEFAULT_LANGUAGE
from database.UserType import UserTypeEnum, UserTypeService
from database.Users import UsersService

available_languages = ('uz', 'ru')

users_service = UsersService()
user_type_service = UserTypeService()


class Middleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Any:
        user = None
        user_id = None
        
        # Extract user_id safely from Telegram update event
        if hasattr(event, 'from_user') and event.from_user:
            user_id = event.from_user.id
        elif isinstance(event, dict):
            if event.get('message') and event['message'].get('from_user'):
                user_id = event['message']['from_user']['id']
            elif event.get('callback_query') and event['callback_query'].get('from_user'):
                user_id = event['callback_query']['from_user']['id']

        if user_id:
            user = users_service.getById(user_id)

        data['user'] = user
        if user and user.get('lang'):
            data['lang'] = user['lang']
        else:
            data['lang'] = DEFAULT_LANGUAGE

        return await handler(event, data)


class AdminMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Any:
        user_id = event.from_user.id if hasattr(event, 'from_user') and event.from_user else None
        user = data.get('user')
        if not user and user_id:
            user = users_service.getById(user_id)

        is_admin = (user_id == ADMIN) or (user and user.get('user_type') == int(UserTypeEnum.ADMIN))

        if not is_admin:
            if user_id:
                await event.bot.send_message(user_id, "Siz administrator emassiz!")
            return

        return await handler(event, data)