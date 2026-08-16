#!/usr/bin/env python3
"""
Script to send targeted messages to specific Telegram users by user ID.
Supports Flow 1 (Watermarked photo / unpaid video note) and Flow 2 (Circle video reminder).
Translates messages based on the user's selected language from the database.
"""

import argparse
import asyncio
import logging
import os
import sys

from aiogram import Bot
from aiogram.types import FSInputFile

# Ensure project root is in python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from Config import FAST_DELIVERY, TOKEN
from database.Users import UsersService
from handlers.keyboard import flow1_payment_keyboard, flow2_continue_keyboard
from handlers.Translation import _

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


async def process_user(
    bot: Bot,
    users_service: UsersService,
    user_id: int,
    flow: int,
    count: int,
    amount: int,
    photo: str | None,
    dry_run: bool = False,
):
    user_lang_info = await users_service.getLanguageById(user_id)
    lang = user_lang_info["lang"] if (user_lang_info and user_lang_info.get("lang")) else "uz"

    if flow == 1:
        raw_text_key = (
            "Уважаемый клиент. Обнаружено {count} ваших фотографий, как только вы произведете оплату, "
            "вы сможете получить оригинальные фотографии высокого качества. Если у вас есть вопросы, "
            "свяжитесь с /admin Мы ждем вас…"
        )
        text = _(raw_text_key, lang).format(count=count)
        keyboard = flow1_payment_keyboard(amount=amount, lang_=lang)

        logging.info("[Flow 1] Target User: %s | Lang: %s", user_id, lang)

        if dry_run:
            print(f"[DRY-RUN] Would send Flow 1 to {user_id} ({lang}):")
            print(f"  Text:\n{text}")
            print(f"  Photo: {photo}")
            return True

        if photo:
            if os.path.isfile(photo):
                photo_input = FSInputFile(photo)
            else:
                photo_input = photo
            await bot.send_photo(
                chat_id=user_id,
                photo=photo_input,
                caption=text,
                reply_markup=keyboard,
            )
        else:
            await bot.send_message(
                chat_id=user_id,
                text=text,
                reply_markup=keyboard,
            )

    elif flow == 2:
        raw_text_key = (
            "Уважаемый клиент! Ваш заказ не завершен. Если вы хотите продолжить оформление заказа, нажмите команду /start."
        )
        text = _(raw_text_key, lang)
        keyboard = flow2_continue_keyboard(lang_=lang)

        logging.info("[Flow 2] Target User: %s | Lang: %s", user_id, lang)

        if dry_run:
            print(f"[DRY-RUN] Would send Flow 2 to {user_id} ({lang}):")
            print(f"  Text:\n{text}")
            return True

        await bot.send_message(
            chat_id=user_id,
            text=text,
            reply_markup=keyboard,
        )

    return True


async def main():
    parser = argparse.ArgumentParser(
        description="Send targeted Flow 1 or Flow 2 messages to specific user IDs in their preferred DB language."
    )
    parser.add_argument(
        "--user-ids",
        nargs="+",
        type=int,
        required=True,
        help="List of Telegram user IDs to send messages to.",
    )
    parser.add_argument(
        "--flow",
        type=int,
        choices=[1, 2],
        required=True,
        help="Flow number: 1 (Watermark/Payment prompt) or 2 (Circle video reminder).",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=1,
        help="Number of detected photos for Flow 1 (default: 1).",
    )
    parser.add_argument(
        "--amount",
        type=int,
        default=FAST_DELIVERY,
        help=f"Payment amount for Flow 1 button (default: {FAST_DELIVERY}).",
    )
    parser.add_argument(
        "--photo",
        type=str,
        default=None,
        help="Optional local photo file path or Telegram photo file_id for Flow 1.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print text and target info without sending Telegram messages.",
    )

    args = parser.parse_args()

    if not TOKEN and not args.dry_run:
        logging.error("Telegram bot TOKEN is not set in environment or Config.py!")
        sys.exit(1)

    from bot_instance import bot

    users_service = UsersService()
    success_count = 0
    fail_count = 0

    try:
        for user_id in args.user_ids:
            try:
                await process_user(
                    bot=bot,
                    users_service=users_service,
                    user_id=user_id,
                    flow=args.flow,
                    count=args.count,
                    amount=args.amount,
                    photo=args.photo,
                    dry_run=args.dry_run,
                )
                success_count += 1
                logging.info("Successfully processed user ID: %s", user_id)
            except Exception as e:
                fail_count += 1
                logging.error("Failed to process user ID %s: %s", user_id, e)

        logging.info(
            "Batch execution complete. Total: %d, Succeeded: %d, Failed: %d",
            len(args.user_ids),
            success_count,
            fail_count,
        )
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
