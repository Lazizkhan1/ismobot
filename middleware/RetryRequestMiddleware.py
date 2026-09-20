import asyncio
import logging

from aiogram import Bot
from aiogram.client.session.middlewares.base import BaseRequestMiddleware, NextRequestMiddlewareType
from aiogram.exceptions import TelegramServerError, TelegramNetworkError, TelegramRetryAfter
from aiogram.methods import TelegramMethod
from aiogram.methods.base import TelegramType

max_retries: int = 3
delay: float = 1.0


class RetryRequestMiddleware(BaseRequestMiddleware):
    async def __call__(
            self,
            make_request: NextRequestMiddlewareType[TelegramType],
            bot: Bot,
            method: TelegramMethod[TelegramType],
    ) -> TelegramType:
        retries = 0
        while True:
            try:
                return await make_request(bot, method)
            except TelegramRetryAfter as e:
                # Telegram specifically asked to wait for `e.retry_after` seconds
                logging.warning(f"Rate limited. Waiting for {e.retry_after} seconds...")
                await asyncio.sleep(e.retry_after)
            except (TelegramServerError, TelegramNetworkError) as e:
                # Retries on server errors (5xx) or temporary network glitches
                retries += 1
                if retries > max_retries:
                    logging.error(f"Failed after {max_retries} retries for method {method.__class__.__name__}")
                    raise e

                sleep_time = delay * (2 ** (retries - 1))  # Exponential backoff
                logging.warning(f"Error {e}: Retrying attempt {retries}/{max_retries} in {sleep_time}s...")
                await asyncio.sleep(sleep_time)
