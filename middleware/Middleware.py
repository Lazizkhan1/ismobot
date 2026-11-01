from logging import log, INFO
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject, User

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
                referred_by = None
                if isinstance(event, Message) and event.text and event.text.startswith("/start"):
                    parts = event.text.split(maxsplit=1)
                    if len(parts) > 1 and parts[1].strip().isdigit():
                        cand_id = int(parts[1].strip())
                        if cand_id != from_user.id:
                            ref_user = await Users.getById(cand_id)
                            if ref_user:
                                referred_by = ref_user.id

                user = await users_service.create(
                    id=from_user.id,
                    username=from_user.username or "",
                    fullname=from_user.full_name,
                    lang="en",
                    typeId=UserTypeEnum.CUSTOMER,
                    referred_by=referred_by,
                )

        data['user'] = user
        data['lang'] = user.lang if user else "en"

        return await handler(event, data)
