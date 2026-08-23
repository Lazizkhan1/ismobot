from logging import log, INFO
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User

from database import Users
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
            user = await Users.getById(from_user.id)
            if not user:
                user = await users_service.create(
                    id=from_user.id,
                    username=from_user.username or "",
                    fullname=from_user.full_name,
                    lang="en",
                    typeId=UserTypeEnum.CUSTOMER,
                )

        data['user'] = user
        data['lang'] = user.lang if user else "en"

        return await handler(event, data)
