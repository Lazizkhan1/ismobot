from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from database.Categories import CategoriesService
from database.Orders import OrdersService, OrderStatus
from database.Users import UsersService
from handlers.keyboard import admin_main_menu, cancel_button, admin_categories_main_menu, back_to_categories_menu
from middleware.LoggingMiddleware import LoggingMiddleware
from middleware.Middleware import AdminMiddleware, Middleware
from handlers.States import CategoryState
from handlers.Translation import _

route = Router()
route.message.middleware.register(AdminMiddleware())
route.message.middleware.register(Middleware())
route.callback_query.middleware.register(LoggingMiddleware())
route.callback_query.middleware.register(Middleware())
users_service = UsersService()
categories_service = CategoriesService()
orders_service = OrdersService()


async def command_start_handler(message: Message, lang: str) -> None:
    await message.answer(_("Главное меню!", lang), reply_markup=admin_main_menu(lang))


@route.callback_query(
    F.data == 'categories'
)
async def categories(query: CallbackQuery, lang: str) -> None:
    await query.message.edit_text(_("Категории", lang), reply_markup=admin_categories_main_menu(lang))


@route.callback_query(
    F.data == 'add_category'
)
async def add_category(query: CallbackQuery, state: FSMContext, lang: str) -> None:
    await state.set_state(CategoryState.name)
    await query.answer(_("Введите название категории!", lang), reply_markup=cancel_button(lang))


@route.message(
    CategoryState.name
)
async def add_category_name(message: Message, state: FSMContext, lang: str) -> None:
    category_name = message.text.strip()
    categories_service.create(category_name)
    await state.clear()
    await message.answer(_("Категория успешно добавлена!", lang), reply_markup=admin_categories_main_menu(lang))


@route.callback_query(
    F.data == 'remove_category'
)
async def remove_category(query: CallbackQuery, state: FSMContext, lang: str) -> None:
    await state.set_state(CategoryState.name)
    await query.answer(_("Введите ID категории, которую хотите удалить!", lang), reply_markup=cancel_button(lang))


@route.message(
    CategoryState.name
)
async def remove_category_id(message: Message, state: FSMContext, lang: str) -> None:
    cat_id = message.text.strip()
    if not cat_id.isdigit():
        await message.answer(_("Категория не найдена!", lang))
        return
    res = categories_service.delete(int(cat_id))
    await state.clear()
    if res:
        await message.answer(_("Категория успешно удалена!", lang), reply_markup=admin_categories_main_menu(lang))
    else:
        await message.answer(_("Категория не найдена!", lang), reply_markup=admin_categories_main_menu(lang))


@route.callback_query(
    F.data == 'all_categories'
)
async def all_categories_handler(query: CallbackQuery, lang: str) -> None:
    cats = categories_service.getAll()
    if not cats:
        await query.answer(_("Категорий нет!", lang))
        return
    text = ""
    for category in cats:
        text += f"ID: {category['id']} | {category['name']}\n"

    await query.message.edit_text(text, reply_markup=back_to_categories_menu(lang))


@route.callback_query(
    F.data == 'orders'
)
async def all_orders_handler(query: CallbackQuery, lang: str) -> None:
    orders = orders_service.getByStatus(OrderStatus.PENDING)
    if not orders:
        await query.answer(_("Заказов нет!", lang))
        return
    text = f"К-во ожидающих заказов: {len(orders)}"
    await query.message.edit_text(text, reply_markup=admin_main_menu(lang))


@route.callback_query(
    F.data == 'main_menu'
)
async def main_menu(query: CallbackQuery, lang: str) -> None:
    await query.message.edit_text(_("Главное меню!", lang), reply_markup=admin_main_menu(lang))


@route.callback_query(
    F.data == 'cancel'
)
async def cancel(query: CallbackQuery, state: FSMContext, lang: str) -> None:
    await state.clear()
    await query.message.delete()