import logging
from itertools import batched

from aiogram import F, Router
from aiogram.enums import ContentType, InputMediaType, ChatAction
from aiogram.fsm.context import FSMContext
from aiogram.types import BotCommand, CallbackQuery, Message
from aiogram.utils.media_group import MediaGroupBuilder

from bot_instance import bot
from database import Orders
from database.OrderPhotos import OrderPhotosService
from handlers.States import CancelOrder, OrderPhotos
from handlers.Translation import _
from handlers.constants import bot_commands
from handlers.keyboard import rate_the_service

router = Router()

orders_service = Orders.OrdersService()
order_photos_service = OrderPhotosService()


@router.callback_query(F.data.startswith("accept_order:"))
async def accept_order(query: CallbackQuery, state: FSMContext, lang: str) -> None:
    order_id = int(query.data.split(":")[-1])
    order = await orders_service.getById(order_id)
    if not order or order["status"] != Orders.OrderStatus.PENDING:
        await query.answer(_("Заказ уже принят или отменен!", lang))
        return
    await query.message.edit_caption(caption=query.message.caption + "\n\n" + _("✅Заказ принят!", lang), reply_markup=None)
    await orders_service.acceptOrder(order_id)
    await state.update_data(order_id=order_id)
    await state.set_state(OrderPhotos.photos)
    await query.message.answer(_("Пожалуйста, отправьте фотографии пользователя!", lang))
    await query.answer(_("✅Заказ принят!", lang))
    await bot.set_my_commands([
        BotCommand(command="/done", description="Rasmlarni yuborishni yakunlash")
    ])


@router.message(OrderPhotos.photos)
async def order_photos_upload(message: Message, state: FSMContext, lang: str) -> None:
    data = await state.get_data()
    order_id = data.get("order_id")

    if message.content_type in (ContentType.DOCUMENT, ContentType.PHOTO):
        file_id = (
            message.photo[-1].file_id
            if message.content_type == ContentType.PHOTO
            else message.document.file_id
        )
        await order_photos_service.add_order_photo(order_id, file_id)
        logging.info("Photo added for order %s by user %s", order_id, message.from_user.id)
        return

    if message.text == "/done":
        await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.UPLOAD_DOCUMENT)
        order = await orders_service.completeOrder(order_id)
        photos = await order_photos_service.get_order_photos(order_id)
        builder = None
        photos_chunk = batched(photos, 10)

        for chunk in photos_chunk:
            builder = MediaGroupBuilder()
            for item in chunk:
                try:
                    # await bot.send_photo(chat_id=order["user_id"], photo=item["photo_id"])
                    print("Sending with builder")
                    builder.add(type=InputMediaType.DOCUMENT, media=item["photo_id"])
                except Exception:
                    print("Sending with send_document")
                    await bot.send_document(chat_id=order["user_id"], document=item["photo_id"])

            await bot.send_media_group(chat_id=order["user_id"], media=builder.build())

        await state.clear()
        await bot.send_message(
            chat_id=order["user_id"],
            text=_("Мы искренне рады сотрудничеству с вами. Пожалуйста, оцените качество нашего сервиса.", lang),
            reply_markup=rate_the_service(lang),
        )
        await message.answer(_("Заказ успешно завершен и фотографии отправлены!", lang))
        await bot.set_my_commands(bot_commands)


@router.callback_query(F.data.startswith("cancel_order_admin:"))
async def cancel_order_admin(query: CallbackQuery, state: FSMContext, lang: str) -> None:
    order_id = int(query.data.split(":")[-1])
    await state.set_state(CancelOrder.reason)
    await state.update_data(order_id=order_id)
    await query.message.edit_caption(caption=query.message.caption + "\n\n" + _("❌Заказ был отменен администратором.", lang), reply_markup=None)
    await query.message.answer(_("Введите причину отмены заказа:", lang))


@router.message(CancelOrder.reason)
async def cancel_order_reason(message: Message, state: FSMContext, lang: str) -> None:
    data = await state.get_data()
    await state.clear()
    order = await orders_service.getById(data["order_id"])
    if order:
        await orders_service.cancelOrder(order["id"], message.text)
        await message.answer(_("Заказ был отменен!", lang))
        try:
            await bot.send_message(
                chat_id=order["user_id"],
                text=_("Ваш заказ был отменен по причине: ", lang) + message.text,
            )
        except Exception:
            pass
