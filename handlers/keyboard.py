from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from Config import DEFAULT_LANGUAGE, FAST_DELIVERY, SLOW_DELIVERY
from database.Categories import CategoriesService
from handlers.Translation import _
from aiogram.utils.keyboard import InlineKeyboardBuilder

categories_service = CategoriesService()
_lang = DEFAULT_LANGUAGE


async def all_categories(prefix=""):
    categories = await categories_service.getAll()
    rows = []
    for category in categories:
        row = [InlineKeyboardButton(text=f"🏛️ {category['name']}", callback_data=f"{prefix}category:{category['id']}")]
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_categories_main_menu(lang_=_lang):
    row1 = [
        InlineKeyboardButton(text=_('Все категории', lang_), callback_data='all_categories'),
        InlineKeyboardButton(text=_('Добавить категорию', lang_), callback_data='add_category'),
        InlineKeyboardButton(text=_('Удалить категорию', lang_), callback_data='remove_category')
    ]
    row2 = [
        InlineKeyboardButton(text=_('Главное меню', lang_), callback_data='main_menu')
    ]
    rows = [row1, row2]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_main_menu(lang_=_lang):
    row1 = [
        InlineKeyboardButton(text=_('Категории', lang_), callback_data='categories'),
    ]
    row2 = [
        InlineKeyboardButton(text=_('Заказы', lang_), callback_data='orders'),
    ]
    row3 = [
        InlineKeyboardButton(text=_('Отмена', lang_), callback_data='cancel')
    ]
    rows = [row1, row2, row3]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def back_to_categories_menu(lang_=_lang):
    row = [InlineKeyboardButton(text=_('Назад', lang_), callback_data='categories')]
    rows = [row]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def cancel_button(lang_=_lang):
    row = [InlineKeyboardButton(text=_('Отмена', lang_), callback_data='cancel')]
    rows = [row]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def rate_the_service(lang_=_lang):
    builder = InlineKeyboardBuilder()
    builder.button(text="⭐❌", callback_data="rate:1")
    builder.button(text="⭐⭐👎", callback_data="rate:2")
    builder.button(text="⭐⭐⭐🆗", callback_data="rate:3")
    builder.button(text="⭐⭐⭐⭐👍", callback_data="rate:4")
    builder.button(text="⭐⭐⭐⭐⭐✅", callback_data="rate:5")
    builder.adjust(1)
    return builder.as_markup()


def delivery_type(lang_=_lang):
    fast_text = f"{FAST_DELIVERY:,} {_("сум", lang_)}".replace(",", " ")
    slow_text = f"{_('От 24 часов🕒', lang_)} - {SLOW_DELIVERY:,} so'm".replace(",", " ")
    row = [
        [InlineKeyboardButton(text=f"{fast_text}", callback_data='delivery_fast')],
        # [InlineKeyboardButton(text=f"🕒 {slow_text}", callback_data='delivery_slow')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=row)


def order_accept(order_id, lang_=_lang):
    row = [
        [InlineKeyboardButton(text=_('Принять', lang_), callback_data=f'accept_order:{order_id}')],
        [InlineKeyboardButton(text=_('Отклонить', lang_), callback_data=f'cancel_order_admin:{order_id}')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=row)


def language_markup():
    rows = [
        [
            InlineKeyboardButton(text='🇺🇿 O\'zbek tili', callback_data='lang_uz'),
            InlineKeyboardButton(text='🇷🇺 Русский язык', callback_data='lang_ru')
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)
