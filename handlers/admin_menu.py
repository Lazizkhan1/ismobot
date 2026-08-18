from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database.Categories import CategoriesService
from database.Orders import OrderStatus, OrdersService
from handlers.States import CategoryState
from handlers.Translation import _
from handlers.keyboard import (
    admin_categories_main_menu,
    admin_main_menu,
    back_to_categories_menu,
    cancel_button,
)

router = Router()

categories_service = CategoriesService()
orders_service = OrdersService()


async def command_start_handler(message: Message, lang: str) -> None:
    await message.answer(_("Главное меню!", lang), reply_markup=admin_main_menu(lang))


@router.callback_query(F.data == "categories")
async def categories(query: CallbackQuery, lang: str) -> None:
    await query.message.edit_text(_("Категории", lang), reply_markup=admin_categories_main_menu(lang))


@router.callback_query(F.data == "add_category")
async def add_category(query: CallbackQuery, state: FSMContext, lang: str) -> None:
    await state.set_state(CategoryState.name)
    await state.set_data({"action": "add"})
    await query.message.answer(_("Введите название категории!", lang), reply_markup=cancel_button(lang))


@router.callback_query(F.data == "remove_category")
async def remove_category(query: CallbackQuery, state: FSMContext, lang: str) -> None:
    await state.set_state(CategoryState.name)
    await state.set_data({"action": "remove"})
    await query.message.answer(_("Введите ID категории, которую хотите удалить!", lang), reply_markup=cancel_button(lang))


@router.message(CategoryState.name)
async def category_name(message: Message, state: FSMContext, lang: str) -> None:
    category_name = message.text.strip()
    data = await state.get_data()
    action = data.get("action")

    if action == "add":
        await categories_service.create(category_name)
        await state.clear()
        await message.answer(_("Категория успешно добавлена!", lang), reply_markup=admin_categories_main_menu(lang))
        return

    if action == "remove":
        cat_id = category_name
        if not cat_id.isdigit():
            await message.answer(_("Категория не найдена!", lang))
            return

        res = await categories_service.delete(int(cat_id))
        await state.clear()
        if res:
            await message.answer(_("Категория успешно удалена!", lang), reply_markup=admin_categories_main_menu(lang))
        else:
            await message.answer(_("Категория не найдена!", lang), reply_markup=admin_categories_main_menu(lang))



@router.callback_query(F.data == "all_categories")
async def all_categories_handler(query: CallbackQuery, lang: str) -> None:
    cats = await categories_service.getAll()
    if not cats:
        await query.message.answer(_("Категорий нет!", lang))
        return
    text = ""
    for category in cats:
        text += f"ID: {category['id']} | {category['name']}\n"

    await query.message.edit_text(text, reply_markup=back_to_categories_menu(lang))


@router.callback_query(F.data == "orders")
async def all_orders_handler(query: CallbackQuery, lang: str) -> None:
    orders = await orders_service.getByStatus(OrderStatus.PENDING)
    if not orders:
        await query.message.answer(_("Заказов нет!", lang))
        return

    text = f"К-во ожидающих заказов: {len(orders)}"
    await query.message.edit_text(text, reply_markup=admin_main_menu(lang))


@router.callback_query(F.data == "main_menu")
async def main_menu(query: CallbackQuery, lang: str) -> None:
    await query.message.edit_text(_("Главное меню!", lang), reply_markup=admin_main_menu(lang))


@router.callback_query(F.data == "cancel")
async def cancel(query: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await query.message.delete()
