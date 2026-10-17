
import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Optional

from aiogram import Bot, Router
from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter
from aiogram.types import FSInputFile

# Ensure project root is in python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from Config import ADMIN, TOKEN

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

router = Router()

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}


async def send_photo_choice(
    chat_id: int = ADMIN,
    photos_dir: Optional[str | Path] = None,
    bot: Optional[Bot] = None,
    delay: float = 0.2,
    as_document: bool = False,
) -> int:
    """
    Sends all photos from the specified photos folder to the given chat_id
    as protected content with the filename in the caption.
    Automatically falls back to send_document if photo dimensions exceed Telegram's limits.

    :param chat_id: Target Telegram user ID or chat ID (defaults to ADMIN).
    :param photos_dir: Directory containing photos (defaults to project's 'photos' directory).
    :param bot: Optional aiogram Bot instance. If not provided, a temporary one will be created.
    :param delay: Pause in seconds between sending photos to respect rate limits.
    :param as_document: If True, sends directly as document files.
    :return: Number of photos successfully sent.
    """
    if not chat_id:
        raise ValueError("A valid chat_id (or ADMIN in Config) is required.")

    if photos_dir is None:
        photos_path = Path(__file__).parent / "photos"
    else:
        photos_path = Path(photos_dir)

    if not photos_path.is_dir():
        logging.error("Photos directory does not exist: %s", photos_path)
        return 0

    photo_files = sorted(
        [
            f
            for f in photos_path.iterdir()
            if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
        ],
        key=lambda x: x.name,
    )

    if not photo_files:
        logging.warning("No supported photos found in: %s", photos_path)
        return 0

    logging.info("Found %d photos in %s to send to chat %s", len(photo_files), photos_path, chat_id)

    owns_bot = False
    if bot is None:
        if not TOKEN:
            raise ValueError("TOKEN environment variable is required")
        bot = Bot(token=TOKEN)
        owns_bot = True

    sent_count = 0
    try:
        for idx, file_path in enumerate(photo_files, start=1):
            caption = file_path.name
            photo_file = FSInputFile(str(file_path))

            max_retries = 3
            for attempt in range(max_retries):
                try:
                    if as_document:
                        await bot.send_document(
                            chat_id=chat_id,
                            document=photo_file,
                            caption=caption,
                            protect_content=True,
                        )
                    else:
                        try:
                            await bot.send_photo(
                                chat_id=chat_id,
                                photo=photo_file,
                                caption=caption,
                                protect_content=True,
                            )
                        except TelegramBadRequest as e:
                            if "PHOTO_INVALID_DIMENSIONS" in str(e) or "dimensions" in str(e).lower():
                                logging.warning(
                                    "[%d/%d] %s exceeds photo dimension limits (sum > 10000px). Sending as document...",
                                    idx,
                                    len(photo_files),
                                    caption,
                                )
                                await bot.send_document(
                                    chat_id=chat_id,
                                    document=photo_file,
                                    caption=caption,
                                    protect_content=True,
                                )
                            else:
                                raise e

                    sent_count += 1
                    logging.info("[%d/%d] Sent %s to %s", idx, len(photo_files), caption, chat_id)
                    break
                except TelegramRetryAfter as e:
                    logging.warning("Rate limited by Telegram. Sleeping for %s seconds", e.retry_after)
                    await asyncio.sleep(e.retry_after)
                except Exception as e:
                    logging.error("Failed to send %s (attempt %d/%d): %s", caption, attempt + 1, max_retries, e)
                    if attempt == max_retries - 1:
                        break
                    await asyncio.sleep(1)

            if delay > 0:
                await asyncio.sleep(delay)

    finally:
        await bot.send_message(chat_id=chat_id, text="Hurmatli mijoz iltimos siz tanlagan 5 ta rasmni tagida ko'rsatilgan raqamlarni bizga jo'nating. Biz sizga rasmlarni yuboramiz!")
        if owns_bot:
            await bot.session.close()

    logging.info("Successfully sent %d/%d photos to %s", sent_count, len(photo_files), chat_id)
    return sent_count


def parse_args():
    parser = argparse.ArgumentParser(
        description="Send all photos from a directory as protected content with filename in caption."
    )
    parser.add_argument(
        "--chat-id",
        "--user-id",
        dest="chat_id",
        type=int,
        default=ADMIN,
        help=f"Target Telegram chat/user ID (default: {ADMIN})",
    )
    parser.add_argument(
        "--dir",
        dest="photos_dir",
        type=str,
        default=None,
        help="Directory containing photos (default: ./photos)",
    )
    parser.add_argument(
        "--delay",
        dest="delay",
        type=float,
        default=0.2,
        help="Delay in seconds between photo sends (default: 0.2)",
    )
    parser.add_argument(
        "--as-document",
        dest="as_document",
        action="store_true",
        help="Send photos as document files directly",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(
        send_photo_choice(
            chat_id=args.chat_id,
            photos_dir=args.photos_dir,
            delay=args.delay,
            as_document=args.as_document,
        )
    )