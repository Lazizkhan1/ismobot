from logging import log, INFO
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User

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
        from_user: User | None = None

        if hasattr(event, 'from_user') and event.from_user:
            from_user = event.from_user

        if from_user and isinstance(from_user, User):
            log(INFO, f"Fetching user {from_user.id} from database")
            user = await users_service.getById(from_user.id)
            if not user:
                user = await users_service.create(
                    from_user.id,
                    from_user.username or "",
                    "**",
                    UserTypeEnum.CUSTOMER,
                )

        data['user'] = user
        data['lang'] = user.lang

        return await handler(event, data)
